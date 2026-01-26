import os, shutil
from fastapi import FastAPI, UploadFile, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional

from backend.database import SessionLocal, engine, Base
from backend.models import User, LectureHistory
from backend.speech_to_text import transcribe
from backend.notes_generator import generate_notes
from backend.quiz_generator import generate_quiz
from backend.topic_extractor import extract_topics
from backend.file_export import export_pdf
from backend.flashcard_generator import generate_flashcards
from backend.timestamp_highlights import extract_key_moments
from backend.youtube_summarizer import summarize_youtube_video

SECRET = os.getenv("SECRET_KEY", "CHANGE_ME_IN_PRODUCTION")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI(title="NoteGPT API", version="2.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


# Utility Functions
def create_token(username: str):
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode(
        {"sub": username, "exp": expire},
        SECRET,
        algorithm=ALGORITHM
    )


def current_user(token: str = Depends(oauth)):
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication")


# Authentication Endpoints
@app.post("/signup/")
def signup(username: str, password: str):
    """Register a new user"""
    if len(username) < 3 or len(password) < 6:
        return {"success": False, "message": "Username must be 3+ chars, password 6+ chars"}

    db = SessionLocal()
    try:
        if db.query(User).filter_by(username=username).first():
            return {"success": False, "message": "Username already exists"}

        db.add(User(username=username, password=pwd.hash(password)))
        db.commit()
        return {"success": True, "message": "User created successfully"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()


@app.post("/login/")
def login(username: str, password: str):
    """Login and get access token"""
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(username=username).first()
        if not user or not pwd.verify(password, user.password):
            return {"success": False, "message": "Invalid credentials"}

        return {
            "success": True,
            "access_token": create_token(username),
            "token_type": "bearer"
        }
    finally:
        db.close()


# Background Processing
def process_bg(path: str, filename: str, username: str, source_type: str = "upload", source_url: str = None):
    """Background task to process lecture"""
    db = SessionLocal()
    try:
        # Create lecture entry
        lec = LectureHistory(
            username=username,
            status="processing",
            source_type=source_type,
            source_url=source_url,
            title=filename
        )
        db.add(lec)
        db.commit()
        db.refresh(lec)

        # Transcribe
        lec.status = "transcribing"
        db.commit()
        result = transcribe(path)

        # Generate notes
        lec.status = "generating_notes"
        db.commit()
        notes = generate_notes(result["text"])

        # Generate summary (first 500 chars of notes)
        summary = notes[:500] + "..." if len(notes) > 500 else notes

        # Extract topics
        lec.status = "extracting_topics"
        db.commit()
        topics = extract_topics(result["text"])

        # Generate flashcards
        lec.status = "generating_flashcards"
        db.commit()
        flashcards = generate_flashcards(result["text"], num_cards=10)

        # Extract key moments
        lec.status = "extracting_highlights"
        db.commit()
        key_moments = extract_key_moments(result["segments"], max_highlights=10)

        # Update lecture
        lec.transcript = result["text"]
        lec.notes = notes
        lec.summary = summary
        lec.segments = result["segments"]
        lec.topics = topics
        lec.flashcards = flashcards
        lec.key_moments = key_moments
        lec.duration_minutes = len(result["segments"]) / 12 if result["segments"] else 0
        lec.status = "completed"

        db.commit()
    except Exception as e:
        lec.status = f"failed: {str(e)}"
        db.commit()
        print(f"Error processing lecture: {e}")
    finally:
        db.close()
        # Clean up uploaded file
        if os.path.exists(path):
            os.remove(path)


# Lecture Processing Endpoints
@app.post("/process/")
async def process(file: UploadFile, bg: BackgroundTasks, user=Depends(current_user)):
    """Upload and process a lecture file"""
    try:
        allowed_extensions = ["mp3", "wav", "mp4", "mkv", "avi", "mov", "webm", "m4a"]
        file_ext = file.filename.split(".")[-1].lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(400, f"File type .{file_ext} not supported")

        os.makedirs("/data", exist_ok=True)
        path = f"/data/{file.filename}"

        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        bg.add_task(process_bg, path, file.filename, user, "upload")

        return {
            "success": True,
            "message": "Processing started. Check history for updates."
        }
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")


@app.post("/process/youtube/")
async def process_youtube(video_url: str, bg: BackgroundTasks, user=Depends(current_user)):
    """Process a YouTube video"""
    try:
        # Download YouTube audio
        result = summarize_youtube_video(video_url)

        if not result.get("success"):
            raise HTTPException(400, result.get("error", "YouTube download failed"))

        audio_path = result["audio_path"]
        title = result["metadata"].get("title", "YouTube Video")

        # Start background processing
        bg.add_task(process_bg, audio_path, title, user, "youtube", video_url)

        return {
            "success": True,
            "message": f"Processing YouTube video: {title}",
            "metadata": result["metadata"]
        }
    except Exception as e:
        raise HTTPException(500, f"YouTube processing failed: {str(e)}")


@app.get("/history/")
def history(user=Depends(current_user), status: str = None, limit: int = 50):
    """Get all lectures for current user"""
    db = SessionLocal()
    try:
        query = db.query(LectureHistory).filter_by(username=user)

        if status:
            query = query.filter(LectureHistory.status.contains(status))

        items = query.order_by(LectureHistory.created_at.desc()).limit(limit).all()

        return [{
            "id": i.id,
            "title": i.title,
            "notes": i.notes,
            "summary": i.summary,
            "transcript": i.transcript,
            "topics": i.topics,
            "flashcards": i.flashcards,
            "key_moments": i.key_moments,
            "status": i.status,
            "duration_minutes": i.duration_minutes,
            "source_type": i.source_type,
            "source_url": i.source_url,
            "created_at": i.created_at.isoformat() if i.created_at else None,
            "segments": i.segments
        } for i in items]
    finally:
        db.close()


@app.get("/lecture/{lecture_id}")
def get_lecture(lecture_id: int, user=Depends(current_user)):
    """Get specific lecture details"""
    db = SessionLocal()
    try:
        lec = db.query(LectureHistory).filter_by(id=lecture_id, username=user).first()

        if not lec:
            raise HTTPException(404, "Lecture not found")

        return {
            "id": lec.id,
            "title": lec.title,
            "transcript": lec.transcript,
            "notes": lec.notes,
            "summary": lec.summary,
            "topics": lec.topics,
            "flashcards": lec.flashcards,
            "key_moments": lec.key_moments,
            "segments": lec.segments,
            "duration_minutes": lec.duration_minutes,
            "status": lec.status,
            "source_type": lec.source_type,
            "source_url": lec.source_url,
            "created_at": lec.created_at.isoformat() if lec.created_at else None
        }
    finally:
        db.close()


@app.delete("/lecture/{lecture_id}")
def delete_lecture(lecture_id: int, user=Depends(current_user)):
    """Delete a lecture"""
    db = SessionLocal()
    try:
        lec = db.query(LectureHistory).filter_by(id=lecture_id, username=user).first()

        if not lec:
            raise HTTPException(404, "Lecture not found")

        db.delete(lec)
        db.commit()

        return {"success": True, "message": "Lecture deleted"}
    finally:
        db.close()


# Feature Endpoints
@app.post("/quiz/{lecture_id}")
def create_quiz(lecture_id: int, user=Depends(current_user)):
    """Generate quiz for a specific lecture"""
    db = SessionLocal()
    try:
        lec = db.query(LectureHistory).filter_by(id=lecture_id, username=user).first()

        if not lec:
            raise HTTPException(404, "Lecture not found")

        if not lec.transcript:
            raise HTTPException(400, "Lecture has no transcript")

        quiz = generate_quiz(lec.transcript)

        return {
            "success": True,
            "quiz": quiz,
            "lecture_id": lecture_id
        }
    except Exception as e:
        raise HTTPException(500, f"Quiz generation failed: {str(e)}")
    finally:
        db.close()


@app.get("/flashcards/{lecture_id}")
def get_flashcards(lecture_id: int, user=Depends(current_user)):
    """Get flashcards for a lecture"""
    db = SessionLocal()
    try:
        lec = db.query(LectureHistory).filter_by(id=lecture_id, username=user).first()

        if not lec:
            raise HTTPException(404, "Lecture not found")

        return {
            "success": True,
            "flashcards": lec.flashcards or [],
            "lecture_id": lecture_id
        }
    finally:
        db.close()


@app.get("/highlights/{lecture_id}")
def get_highlights(lecture_id: int, user=Depends(current_user)):
    """Get key moments/highlights for a lecture"""
    db = SessionLocal()
    try:
        lec = db.query(LectureHistory).filter_by(id=lecture_id, username=user).first()

        if not lec:
            raise HTTPException(404, "Lecture not found")

        return {
            "success": True,
            "key_moments": lec.key_moments or [],
            "lecture_id": lecture_id
        }
    finally:
        db.close()


@app.get("/export/{lecture_id}")
def export_lecture(lecture_id: int, user=Depends(current_user)):
    """Export lecture notes as PDF"""
    db = SessionLocal()
    try:
        lec = db.query(LectureHistory).filter_by(id=lecture_id, username=user).first()

        if not lec:
            raise HTTPException(404, "Lecture not found")

        if not lec.notes:
            raise HTTPException(400, "Lecture has no notes to export")

        os.makedirs("/data/exports", exist_ok=True)
        output_path = f"/data/exports/lecture_{lecture_id}_notes.pdf"

        # Prepare content
        content = f"{lec.title or f'Lecture {lecture_id}'}\n"
        content += f"Created: {lec.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        content += f"Duration: {lec.duration_minutes:.1f} minutes\n\n"

        if lec.topics:
            content += "Topics:\n"
            for topic in lec.topics:
                content += f"- {topic}\n"
            content += "\n"

        content += "Notes:\n\n"
        content += lec.notes

        export_pdf(content, output_path)

        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename=f"lecture_{lecture_id}_notes.pdf"
        )
    except Exception as e:
        raise HTTPException(500, f"Export failed: {str(e)}")
    finally:
        db.close()


@app.get("/search/")
def search_lectures(q: str, user=Depends(current_user)):
    """Search lectures by title, notes, or transcript"""
    db = SessionLocal()
    try:
        lectures = db.query(LectureHistory).filter_by(username=user).all()

        results = []
        q_lower = q.lower()

        for lec in lectures:
            if (lec.title and q_lower in lec.title.lower()) or \
                    (lec.notes and q_lower in lec.notes.lower()) or \
                    (lec.transcript and q_lower in lec.transcript.lower()):
                results.append({
                    "id": lec.id,
                    "title": lec.title,
                    "summary": lec.summary,
                    "topics": lec.topics,
                    "created_at": lec.created_at.isoformat() if lec.created_at else None
                })

        return {"success": True, "results": results, "count": len(results)}
    finally:
        db.close()


# Health Check
@app.get("/")
def root():
    return {
        "message": "NoteGPT API",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Upload Processing",
            "YouTube Summarization",
            "AI Notes Generation",
            "Topic Extraction",
            "Flashcard Generation",
            "Key Moments Detection",
            "Quiz Generation",
            "PDF Export",
            "Search"
        ]
    }


@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/diagnostics/youtube")
def youtube_diagnostics():
    """Check YouTube download setup"""
    from backend.youtube_summarizer import diagnose_youtube_setup
    diagnostics = diagnose_youtube_setup()

    all_ok = all(diagnostics.values())

    return {
        "status": "ready" if all_ok else "issues_found",
        "checks": diagnostics,
        "message": "All systems ready" if all_ok else "Some requirements missing"
    }