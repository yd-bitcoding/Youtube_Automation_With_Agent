import os
from dotenv import load_dotenv
from database.models import Base  
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base


load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def create_tables():
    """Import models and create tables"""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print("❌ Error creating tables:", e)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
