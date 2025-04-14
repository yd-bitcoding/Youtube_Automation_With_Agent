# from starlette.requests import Request
# from starlette.middleware.base import BaseHTTPMiddleware
# from starlette.responses import Response
# from sqlalchemy.orm import Session
# from datetime import datetime
# import json
# from starlette.responses import JSONResponse
# from database.models import ActivityLog, User
# from database.db_connection import SessionLocal
# from functionality.jwt_funcationality import decodeJWT

# async def log_user_activity_middleware(request: Request, call_next):
#     # Skip logging for docs & static files
#     if request.url.path in ["/docs", "/openapi.json", "/redoc"]:
#         return await call_next(request)

#     # Initialize body variable
#     body = {}
#     user_id = None

#     try:
#         # Read the body depending on the Content-Type (e.g., JSON or form data)
#         content_type = request.headers.get("Content-Type", "")
#         print(f"🔍 Request Content-Type: {content_type}")

#         if "application/json" in content_type:
#             body_bytes = await request.body()
#             if body_bytes:
#                 body = json.loads(body_bytes.decode("utf-8"))
#         elif "application/x-www-form-urlencoded" in content_type:
#             # If it's form data, we handle it differently
#             form_data = await request.form()
#             body = {key: value for key, value in form_data.items()}
#         else:
#             body_bytes = await request.body()
#             body = body_bytes.decode("utf-8") if body_bytes else ""

#         print(f"🔍 Body Content: {body}")  # Log body content for debugging
#     except Exception as e:
#         print(f"❌ Error reading body: {e}")
#         body = {}

#     # Extract the JWT token from the request headers
#     token = request.headers.get("Authorization", "").replace("Bearer ", "")
#     print(f"🔍 Incoming Token: {token}")

#     decoded = None
#     if token:
#         try:
#             decoded = decodeJWT(token)
#             print(f"✅ Decoded Token: {decoded}")
#             # Extract user_id from the decoded payload
#             user_id = decoded.get("payload", {}).get("user_id")
#         except Exception as e:
#             print(f"❌ Failed to decode token: {e}")
    
#     # If no user_id from token, check query params as a fallback
#     if not user_id:
#         user_id = request.query_params.get("user_id")
#         print(f"🔍 Extracted User ID from Query Params: {user_id}")

#     # If no user_id is found, log a warning and set user_id to a default or None
#     if user_id is None:
#         print("❌ User ID not found in token or query parameters.")
#         user_id = "Unknown"  # You can also set it to None if you prefer

#     # Call next middleware or route handler and get the response
#     try:
#         response = await call_next(request)
#         print(f"✅ Response: {response}")
#     except Exception as e:
#         print(f"❌ Error during call_next: {e}")
#         response = JSONResponse(
#         content={"detail": "Internal server error"},
#         status_code=500
#     )

#     # Collect metadata for logging
#     metadata = {
#         "query_params": dict(request.query_params),
#         "body": body if body else None,  # Ensure the body is logged only if not empty
#         "status_code": response.status_code if response else "Unknown"
#     }

#     # Logging activity to the database
#     try:
#         print(f"📝 Logging activity:")
#         print(f"   - User ID: {user_id}")
#         print(f"   - Path: {request.method} {request.url.path}")
#         print(f"   - Metadata: {json.dumps(metadata)}")

#         db: Session = SessionLocal()
#         log = ActivityLog(
#             user_id=user_id,
#             action=f"{request.method} {request.url.path}",
#             description=f"User accessed {request.url.path}",
#             log_metadata=metadata,
#             timestamp=datetime.utcnow()
#         )
#         db.add(log)
#         db.commit()
#         db.close()
#     except Exception as e:
#         print(f"[ActivityLog] Failed: {e}")

#     # Ensure the response is returned
#     return response


from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import Message
from sqlalchemy.orm import Session
from datetime import datetime
import json
from database.models import ActivityLog
from database.db_connection import SessionLocal
from functionality.jwt_funcationality import decodeJWT
from typing import Callable

class LogUserActivityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        if request.url.path in ["/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        body = {}
        user_id = None

        try:
            content_type = request.headers.get("Content-Type", "")
            print(f"🔍 Request Content-Type: {content_type}")

            body_bytes = await request.body()
            request._receive = self._receive_with_body(body_bytes)

            if "application/json" in content_type:
                if body_bytes:
                    body = json.loads(body_bytes.decode("utf-8"))
            elif "application/x-www-form-urlencoded" in content_type:
                form_data = await request.form()
                body = {key: value for key, value in form_data.items()}
            else:
                body = body_bytes.decode("utf-8") if body_bytes else ""

            print(f"🔍 Body Content: {body}")
        except Exception as e:
            print(f"❌ Error reading body: {e}")
            body = {}

        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        print(f"🔍 Incoming Token: {token}")

        decoded = None
        if token:
            try:
                decoded = decodeJWT(token)
                print(f"✅ Decoded Token: {decoded}")
                user_id = decoded.get("payload", {}).get("user_id")
            except Exception as e:
                print(f"❌ Failed to decode token: {e}")

        if not user_id:
            user_id = request.query_params.get("user_id")
            print(f"🔍 Extracted User ID from Query Params: {user_id}")

        if user_id is None:
            print("❌ User ID not found in token or query parameters.")
            user_id = "Unknown"

        try:
            response = await call_next(request)
        except Exception as e:
            print(f"❌ Error during call_next: {e}")
            response = JSONResponse(
                content={"detail": "Internal server error"},
                status_code=500
            )

        metadata = {
            "query_params": dict(request.query_params),
            "body": body if body else None,
            "status_code": response.status_code if response else "Unknown"
        }

        try:
            print(f"📝 Logging activity:")
            print(f"   - User ID: {user_id}")
            print(f"   - Path: {request.method} {request.url.path}")
            print(f"   - Metadata: {json.dumps(metadata)}")

            db: Session = SessionLocal()
            log = ActivityLog(
                user_id=user_id,
                action=f"{request.method} {request.url.path}",
                description=f"User accessed {request.url.path}",
                log_metadata=metadata,
                timestamp=datetime.utcnow()
            )
            db.add(log)
            db.commit()
            db.close()
        except Exception as e:
            print(f"[ActivityLog] Failed: {e}")

        return response

    def _receive_with_body(self, body: bytes):
        async def receive() -> Message:
            return {
                "type": "http.request",
                "body": body,
                "more_body": False
            }
        return receive

