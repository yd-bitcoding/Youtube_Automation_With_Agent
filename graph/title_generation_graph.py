import os
from langgraph.graph import StateGraph
from dotenv import load_dotenv
from service.youtube_service import fetch_youtube_videos
from service.engagement_service import calculate_engagement_rate
from service.trend_service import detect_trending_topics
from service.title_generator_service import generate_ai_titles
from database.db_connection import SessionLocal  #
from sqlalchemy.dialects.postgresql import insert
load_dotenv()


def youtube_fetch_agent(state):
    query = state["query"]
    max_results = state["max_results"]
    duration_category = state.get("duration_category")
    # max_duration = state.get("max_duration")
    min_views = state.get("min_views")
    min_subscribers = state.get("min_subscribers")
    upload_date = state.get("upload_date")  # Get upload_date from the state

    # Call the function with the new filter
    videos = fetch_youtube_videos(
        query=query,
        max_results=max_results,
        duration_category=duration_category,
        # max_duration=max_duration,
        min_views=min_views,
        min_subscribers=min_subscribers,
        upload_date=upload_date  # Pass the upload_date filter
    )

    return {**state, "videos": videos}



def engagement_analysis_agent(state):
    if not isinstance(state, dict):  # Ensure state is a dictionary
        state = {}

    videos = state.get("videos", [])
    if not isinstance(videos, list):  # Ensure videos is a list
        videos = []

    for video in videos:
        video["engagement_rate"] = calculate_engagement_rate(video)  # ✅ Pass the entire video dictionary

    state["videos"] = videos  # Ensure updated videos are stored back in state
    return state  # Return updated state




# 🎯 Step 3: Detect Trending Topics
# def title_generation_agent(state,db):
#     db = SessionLocal()  # ✅ Create a new DB session
#     try:
#         trends = state.get("trends", [])
#         top_trend = trends[0][0] if trends else state["query"]  # Fallback to query if no trends
#         titles = generate_ai_titles(top_trend, db)  # ✅ Pass DB session
#         return {**state, "titles": titles}
#     finally:
#         db.close()  # ✅ Close session

def title_generation_agent(state):
    db = SessionLocal()  # ✅ Create a new DB session
    try:
        trends = state.get("trends", [])
        top_trend = trends[0][0] if trends else state.get("query", "")  # Use top trend or fallback to query
        
        user_id = state.get("user_id", 1)  # ✅ Ensure a default user_id if not provided

        if not top_trend:
            return {**state, "titles": []}  # ✅ Prevent errors if no trend is found

        titles = generate_ai_titles(top_trend, user_id, db)  # ✅ Corrected function call
        return {**state, "titles": titles["titles"]}  # ✅ Extract only titles from response
    finally:
        db.close()  # ✅ Always close session



# 🎯 Step 4: Generate AI-Powered Titles
def format_output(state):
    print("📦 Final State Before Output:", state)

    return {
        "videos": state.get("videos", []),
        "trending_topics": [t[0] for t in state.get("trends", [])],  # Extract topic names only
        "generated_titles": state.get("titles", [])
    }


def trending_topic_agent(state):
    """Detect trending topics and store them in DB."""
    db = SessionLocal()  # ✅ Create a new DB session
    try:
        trends = detect_trending_topics(state.get("videos", []), db)  # ✅ Pass DB session
        return {**state, "trends": trends}
    finally:
        db.close()  # ✅ Close session to avoid memory leaks
  # ✅ Fix: Use the correct function




# Define Multi-Agent Graph
viral_graph = StateGraph(dict)  # ✅ Use a dictionary instead of a custom class

viral_graph.add_node("fetch_videos", youtube_fetch_agent)
viral_graph.add_node("analyze_engagement", engagement_analysis_agent)
viral_graph.add_node("detect_trends", trending_topic_agent)

viral_graph.add_node("generate_titles", title_generation_agent)
viral_graph.add_node("format_output", format_output)



# Define Execution Flow
viral_graph.set_entry_point("fetch_videos")
viral_graph.add_edge("fetch_videos", "analyze_engagement")
viral_graph.add_edge("analyze_engagement", "detect_trends")
viral_graph.add_edge("detect_trends", "generate_titles")
viral_graph.add_edge("generate_titles", "format_output")
# ✅ Compile Graph
viral_executor = viral_graph.compile()

# 🚀 Run Multi-Agent System
# def run_viral_idea_finder(query: str):
#     initial_state = {"query": query}
#     result = viral_executor.invoke(initial_state)

#     # 🛠 Debugging: Print final result
#     print("🚀 Final Graph Output:", result)

#     return {
#         "videos": result.get("videos", []),
#         "trending_topics": result.get("trends", []),  # ✅ Ensure trends are returned
#         "generated_titles": result.get("titles", []),  # ✅ Ensure titles are returned
#     }



