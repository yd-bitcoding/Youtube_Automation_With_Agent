import os
import requests
from datetime import datetime
from database.models import User
from sqlalchemy.orm import Session
from database.db_connection import get_db
from .jwt_funcationality import decodeJWT
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

jwt_bearer = HTTPBearer()


#admin and user
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(jwt_bearer), db: Session = Depends(get_db)):
    token = credentials.credentials
    token_data = decodeJWT(token)

    if token_data["expired"]:
        user_id = token_data["payload"].get("user_id") if token_data["payload"] else None
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.is_active = False
                user.logout_time = datetime.utcnow()
                db.commit()
        raise HTTPException(status_code=401, detail="❌ Token expired. Auto-logged out.")

    if not token_data["valid"]:
        raise HTTPException(status_code=401, detail="❌ Invalid token.")

    return token_data["payload"]["user_id"]  