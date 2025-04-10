from fastapi import FastAPI
from routes import viral_idea_finder,title_generation,thumbnail,script
from routes import viral_idea_finder,auth
from database.db_connection import create_tables


app = FastAPI(title="Kreato.AI")


create_tables()

app.include_router(auth.router, prefix="/authentication", tags=["Authentication"])


app.include_router(viral_idea_finder.router, prefix="/viral_idea_finder", tags=["Viral Idea Finder"])

app.include_router(title_generation.router, prefix="/title_generation", tags=["Title Generation"])


app.include_router(thumbnail.thumbnail_router, prefix="/thumbnails", tags=["Thumbnail Finder and Validator"])

app.include_router(script.script_router, prefix="/script", tags=["Script Generation"])


@app.get("/")
def root():
    return {"message": "Welcome to the Kreato.AI!"}