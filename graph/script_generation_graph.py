from langgraph.graph import StateGraph
from service.script_service import generate_script, get_video_details, fetch_transcript, format_script_response
from database.models import RemixedScript, Script

# --- AGENTS ---

def search_agent(state):
    idea = state.get("idea") or state.get("title")
    videos = get_video_details(idea, max_results=2)
    return {**state, "videos": videos}


def transcript_agent(state):
    transcripts = []
    youtube_links = []

    for video in state.get("videos", []):
        transcript_chunks, err = fetch_transcript(video["link"])
        if transcript_chunks:
            if isinstance(transcript_chunks, str):
                transcript_text = transcript_chunks
            elif isinstance(transcript_chunks, list):
                transcript_text = " ".join(chunk["text"] for chunk in transcript_chunks)
            else:
                continue
            transcripts.append(transcript_text)
            youtube_links.append(video["link"])

    return {**state, "transcripts": transcripts, "youtube_links": youtube_links}


def past_script_agent(state):
    db = state["db"]
    user_id = state["user_id"]
    idea = state.get("idea") or state.get("title")
    past_scripts = db.query(Script).filter(
        Script.input_title == idea,
        Script.user_id == user_id
    ).all()
    past_content = "\n".join([ps.generated_script for ps in past_scripts])
    return {**state, "past_scripts_text": past_content}


def script_gen_agent(state):
    combined_transcript = "\n".join(state.get("transcripts", []))
    if state.get("past_scripts_text"):
        combined_transcript += f"\n\n{state['past_scripts_text']}"

    generated_script = generate_script(
        combined_transcript,
        mode=state.get("mode", "Short-form"),
        tone=state.get("tone", "Casual"),
        style=state.get("style", "Casual")
    )
    formatted_script = format_script_response(generated_script)
    return {
        **state,
        "generated_script": formatted_script,
        "combined_transcript": combined_transcript
    }


def remix_script_agent(state):
    video_url = state.get("video_url")
    transcript, err = fetch_transcript(video_url)
    if not transcript:
        raise ValueError(f"Failed to extract transcript: {err}")

    remixed_script = generate_script(
        transcript,
        mode=state.get("mode", "Short-form"),
        tone=state.get("tone", "Casual"),
        style=state.get("style", "Casual")
    )
    formatted_script = format_script_response(remixed_script)

    if "I can't help with this request." in formatted_script:
        raise ValueError("Script generation failed. Try modifying the input.")

    new_remixed_script = RemixedScript(
        user_id=state["user_id"],
        video_url=video_url,
        mode=state["mode"],
        style=state["style"],
        transcript=transcript,
        remixed_script=formatted_script
    )
    db = state["db"]
    db.add(new_remixed_script)
    db.commit()
    db.refresh(new_remixed_script)

    return {
        **state,
        "remixed_script": formatted_script,
        "remixed_script_id": new_remixed_script.id
    }


def entry_agent(state):
    return state


# --- DECISION FUNCTION ---
def choose_entry_path(state):
    remix = state.get("remix", False)
    video_url = state.get("video_url", None)

    if remix and video_url:
        return "right"
    return "left"


# --- GRAPH BUILDING ---
builder = StateGraph(state_schema=dict)

# Add nodes
builder.add_node("entry", entry_agent)
builder.add_node("search", search_agent)
builder.add_node("transcript", transcript_agent)
builder.add_node("past_scripts", past_script_agent)
builder.add_node("generate", script_gen_agent)
builder.add_node("remix", remix_script_agent)

# ✅ Set entry point
builder.set_entry_point("entry")

# Conditional routing from entry
builder.add_conditional_edges(
    "entry",
    choose_entry_path,
    {
        "left": "search",
        "right": "remix"
    }
)

# Normal generation path
builder.add_edge("search", "transcript")
builder.add_edge("transcript", "past_scripts")
builder.add_edge("past_scripts", "generate")

# End points
builder.set_finish_point("generate")
builder.set_finish_point("remix")

# ✅ Compile the graph
graph = builder.compile()
