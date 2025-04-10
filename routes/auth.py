from fastapi import Form
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database.db_connection import get_db
from fastapi.responses import JSONResponse
from database.models import User,UserLoginHistory
from database.schemas import UserLogin,UserRegister
from functionality.current_user import get_current_user
from fastapi import APIRouter, Depends, HTTPException ,Header 
from functionality.jwt_funcationality import create_jwt_token ,decodeJWT
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")




@router.post("/signup")
def signup(user_data: UserRegister, db: Session = Depends(get_db)):

   
    if user_data.username.strip().lower() == "string" or not user_data.username.strip():
        raise HTTPException(status_code=400, detail="Username cannot be empty you need to provide.")
    if user_data.password.strip().lower() == "string" or not user_data.password.strip():
        raise HTTPException(status_code=400, detail="Password cannot be empty you need to provide.")
    
    
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="❌ User already exists. Please try with different Names")

    hashed_password = pwd_context.hash(user_data.password)
    new_user = User(username=user_data.username, password=hashed_password)
    db.add(new_user)
    db.commit()
    return JSONResponse(status_code=201,
        content={"message": "✅ Your registered successfully! Now you can login"}
    )

@router.post("/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    if user_data.username.strip().lower() == "string" or not user_data.username.strip():
        raise HTTPException(status_code=400, detail="Username cannot be empty. You need to provide.")
    if user_data.password.strip().lower() == "string" or not user_data.password.strip():
        raise HTTPException(status_code=400, detail="Password cannot be empty. You need to provide.")
    
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not pwd_context.verify(user_data.password, user.password):
        raise HTTPException(status_code=400, detail="❌ Invalid credentials. Your username or password is wrong.")
    
 
    login_record = UserLoginHistory(user_id=user.id, login_time=datetime.utcnow())
    db.add(login_record)
    
 
    user.is_active = True
    db.commit()
    db.refresh(login_record)

    token = create_jwt_token({"user_id": user.id})
    return JSONResponse(status_code=201,content= { 
        "token": token,
        "message": "You have logged in successfully! Now You Can Explore"
        
    })

@router.post("/logout")
def logout(
    user_id: int = Depends(get_current_user),  
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    # Fetch the latest login record for this user
    latest_login = db.query(UserLoginHistory).filter(
        UserLoginHistory.user_id == user.id,
        UserLoginHistory.logout_time.is_(None)  
    ).order_by(UserLoginHistory.login_time.desc()).first()
    
    if latest_login:
        latest_login.logout_time = datetime.utcnow()
    
    # Update user status to inactive
    user.is_active = False
    db.commit()
    
    return JSONResponse(status_code=201, content={"message": "Logout successful!"})


