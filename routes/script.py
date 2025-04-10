import os
from sqlalchemy.orm import Session
from graph.script_generation_graph import graph
from database.db_connection import get_db
from functionality.current_user import get_current_user
from database.models import RemixedScript, Script, User
from fastapi import Depends, UploadFile, File, Form, HTTPException, status, APIRouter
from service.script_service import (
    generate_script, 
    transcribe_audio, 
    get_video_details, 
    fetch_transcript, 
    format_script_response,
    # generate_speech,
    # handle_voice_tone_upload
)

script_router = APIRouter()

@script_router.get("/get-scripts/")
def get_all_scripts(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
    ):
    scripts = db.query(Script).all()
    return {"scripts": scripts}

@script_router.get("/get-script/{script_id}/")
def get_script(
    script_id: int, 
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
    ):
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        return {"error": "Script not found"}
    return {"script": script}

@script_router.post("/speech-to-text/")
def speech_to_text(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
    ):
    try:
        file_location = f"temp_{file.filename}"
        with open(file_location, "wb") as f:
            f.write(file.file.read())
        transcription = transcribe_audio(file_location)
        os.remove(file_location)
        return {"transcription": transcription}
    except Exception as e:
        return {"error": str(e)}

# @script_router.post("/text-to-speech/")
# async def text_to_speech_endpoint(
#     text: str = Form(...),
#     speech_name: str = Form(...),
#     tone_file: UploadFile = File(None),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     try:
#         user_id = current_user.id
#         voice_sample_path = None

#         if tone_file:
#             voice_sample_path = await handle_voice_tone_upload(tone_file, user_id)
#         print("voice_sample_path ::", voice_sample_path)
#         audio_file_url = generate_speech(text, speech_name, user_id, voice_sample_path)
#         if not audio_file_url:
#             raise HTTPException(status_code=500, detail="Audio file generation failed")

#         return {
#             "message": "Speech generated successfully",
#             "audio_file_url": audio_file_url
#         }

#     except HTTPException as http_exc:
#         raise http_exc
#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@script_router.post("/generate-script-multiagent/")
def generate_script_multiagent_api(
    idea: str = Form(None),
    title: str = Form(None),
    tone: str = Form("Casual"),
    mode: str = Form("Short-form"),
    style: str = Form("Casual"),
    remix: bool = Form(False),
    video_url: str = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user) 
):
    try:
      
        user_id = user.id  
        state = {
            "idea": idea,
            "title": title,
            "tone": tone,
            "mode": mode,
            "style": style,
            "remix": remix,
            "video_url": video_url,
            "db": db,
            "user_id": user_id
        }

        result = graph.invoke(state)  
        if remix:
            return {
                "message": "Remixed script generated successfully",
                "remixed_script_id": result.get("remixed_script_id"),
                "remixed_script": result.get("remixed_script")
            }
        else:
            
            new_script = Script(
                input_title=idea or title,
                video_title=f"Script for {idea or title}",
                mode=mode,
                style=style,
                transcript=result.get("combined_transcript", ""),
                generated_script=result.get("generated_script", ""),
                youtube_links=", ".join(result.get("youtube_links", [])),
                user_id=user_id  
            )
            db.add(new_script)
            db.commit()
            db.refresh(new_script)

            return {
                "message": "Script generated via LangGraph agents!",
                "script_id": new_script.id,
                "generated_script": result.get("generated_script", ""),
                "youtube_links": result.get("youtube_links", [])
            }

    except Exception as e:
        return {"error": str(e)}
