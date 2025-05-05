from sqlalchemy.orm import Session
from fastapi import APIRouter,HTTPException,status,Depends ,Query
from database.schemas import RemixedTitlesResponse,RemixTitleRequest
from database.db_connection import get_db
from graph.title_generation_graph import viral_executor
from database.models import GeneratedTitle, User
from functionality.current_user import get_current_user  
from service.title_generator_service import generate_ai_titles,process_generated_titles,agent

router = APIRouter()

@router.post("/generate_titles/")
def get_titles(
    topic: str,
    user: User = Depends(get_current_user), 
    db: Session = Depends(get_db),
):
    return generate_ai_titles(topic, user.id, db)  


@router.post("/run_viral_analysis/")
def run_analysis(
    query: str, 
    max_results: int = Query(10, description="Number of results to return", ge=1, le=50),
    duration_category: str = Query(None, description="Filter by duration: short, medium, long"),
    min_views: int = Query(None, description="Minimum views required"),
    min_subscribers: int = Query(None, description="Minimum subscriber count"),
    upload_date: str = Query(None, description="Filter by upload date: today, this_week, this_month, this_year"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Invoke the LangGraph viral analysis pipeline."""
    initial_state = {
        "query": query,
        "max_results": max_results,
        "duration_category": duration_category,
        "min_views": min_views,
        "min_subscribers": min_subscribers,
        "upload_date": upload_date  ,
        "user_id": user.id  
    }

    result = viral_executor.invoke(initial_state)
    return {
        "user_id": user.id,
        "videos": result.get("videos", []),
        "generated_titles": result.get("generated_titles", []),
    }


@router.post("/remix_titles", response_model=RemixedTitlesResponse)
def remix_titles_and_edit_prompt(request: RemixTitleRequest, db: Session = Depends(get_db)):
    """
    Generates remixed titles based on a previously generated title.
    Uses the title_id to fetch the video topic and previously generated titles.
    Optionally allows the user to provide a custom prompt.
    """
    try:
        # Query the generated title using the title_id
        generated_title = db.query(GeneratedTitle).filter(GeneratedTitle.id == request.title_id).first()

        if not generated_title:
            raise HTTPException(status_code=404, detail="Generated title not found.")

        # Extract the video topic and previously generated titles
        video_topic = generated_title.video_topic
        previous_titles = generated_title.titles

        # Debugging: Print the video topic and previous titles
        print(f"Video Topic: {video_topic}")
        print(f"Previous Titles: {previous_titles}")

        # Ensure previous_titles is a formatted string (list to string conversion)
        formatted_previous_titles = "\n".join(previous_titles)

        # Determine the prompt to use (either from the user's custom prompt or default)
        if request.custom_prompt:
            if '{video_topic}' in request.custom_prompt or '{previous_titles}' in request.custom_prompt:
        # Case 1: user provided a formatted template string
                prompt = request.custom_prompt.format(
                video_topic=video_topic,
                previous_titles=formatted_previous_titles
            )
            else:
        # Case 2: Treat custom prompt as a theme or instruction
        # Add it into a more detailed full prompt
                prompt = (
            f"Use the theme: {request.custom_prompt}.\n\n"
            f"Topic: {video_topic}\n\n"
            f"Based on the following existing video titles:\n{formatted_previous_titles}\n\n"
            f"Remix and generate 5 creative YouTube video titles that would fit well for the topic above. "
            f"Ensure titles are fun, engaging, and safe for all audiences."
        )
        else:
    # Default fallback if no prompt provided
             prompt = (
        f"Remix the following video titles for the topic '{video_topic}'. "
        f"Use the following titles for inspiration:\n\n"
        f"{formatted_previous_titles}\n\n"
        f"Generate 5 remixed titles."
    )


        # Debugging: Print the prompt being sent to the agent
        print(f"Prompt for Agent: {prompt}")

        # Generate the remixed titles using your AI agent
        response = agent.invoke({"input": prompt})

        if isinstance(response, dict) and "output" in response:
            response = response["output"]
        if not isinstance(response, str):
            raise ValueError(f"Unexpected agent response format: {response}")

        # Process the remixed titles
        remixed_titles = process_generated_titles(response)

        # Return remixed titles with the title_id (if needed)
        return RemixedTitlesResponse(remixed_titles=remixed_titles)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate remixed titles. Error: {e}")

@router.get("/user_titles/")
def get_user_titles(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Fetch video topics and corresponding generated titles with their IDs for the current user,
    grouped by topic. If no titles exist, returns a friendly message.
    """
    # Fetch all generated titles for the user
    rows = db.query(GeneratedTitle).filter(GeneratedTitle.user_id == user.id).all()

    # Initialize a list to store the final response structure
    videos = []

    # Loop through the rows to process titles
    for row in rows:
        topic = row.video_topic.strip() if row.video_topic else None
        titles_list = row.titles if isinstance(row.titles, list) else []

        # Skip rows with invalid or missing topics or titles
        if not topic or not titles_list:
            print(f"Skipping row ID {row.id} due to empty topic or titles.")
            continue

        # Append the video entry with topic, titlesid, and the list of titles
        videos.append({
            "topic": topic,
            "titlesid": row.id,
            "titles": titles_list
        })

    # If no videos were found, return a message
    if not videos:
        return {
            "user_id": user.id,
            "videos": [],
            "message": "No generated titles found for this user."
        }

    # Return the response
    return {
        "user_id": user.id,
        "videos": videos
    }

@router.delete("/user_titles/{title_id}", response_model=dict)
def delete_user_title(
    title_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Delete a specific generated title for the current user by title_id.
    If no such title exists for the user, an error will be returned.
    """
    # Fetch the title from the database based on title_id
    title = db.query(GeneratedTitle).filter(GeneratedTitle.id == title_id, GeneratedTitle.user_id == user.id).first()

    # If the title does not exist for the current user, raise an exception
    if not title:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Title not found or you do not have permission to delete this title"
        )
    
    # Delete the title from the database
    db.delete(title)
    db.commit()

    # Return a success message after deletion
    return {"message": f"Title with ID {title_id} has been successfully deleted."}
