from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends ,Query
from database.db_connection import get_db
from graph.title_generation_graph import viral_executor
from database.models import GeneratedTitle, User
from functionality.current_user import get_current_user  
from service.title_generator_service import generate_ai_titles

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


@router.get("/user_titles/")
def get_user_titles(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Fetch all AI-generated titles for the current user.
    """
    rows = db.query(GeneratedTitle).filter(GeneratedTitle.user_id == user.id).all()
    
    all_titles = []
    for row in rows:
        if isinstance(row.titles, list):
            all_titles.extend(row.titles)
        else:
            all_titles.append(row.titles)  

    return {"user_id": user.id, "generated_titles": all_titles}
