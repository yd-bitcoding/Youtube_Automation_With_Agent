from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class UserRegister(BaseModel):
    username: str 
    password: str 
    
class UserLogin(BaseModel):
    username: str 
    password: str 

class SaveVideoRequest(BaseModel):
    note: Optional[str] = None

class RemixTitleRequest(BaseModel):
    title_id: int
    custom_prompt: Optional[str] = None
    
class RemixedTitlesResponse(BaseModel):
    remixed_titles: List[str]