import os
import shutil
from datetime import datetime, timedelta

from fastapi import FastAPI, UploadFile, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext

from backend.speech_to_text import transcribe
from backend.quiz_generator import generate_quiz
from backend.notes_generator import generate_notes
from backend.file_export import export_pdf
from backend.database import SessionLocal
from backend.models import User, LectureHistory

# ---------------- CONFIG ----------------
SECRET_KEY = "CHANGE_THIS_SECRET_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI(
    title="Lecture Voice-to-Notes API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

@app.get("/")
def root():
    return {"status": "ok", "message": "Backend is running"}


os.makedirs("data/audio", exist_ok=True)
os.makedirs("data/outputs", exist_ok=True)

# ---------------- UTILS ----------------
def _bcrypt_safe(password: str) -> bytes:
    return password.encode("utf-8")[:72]

def hash_password(password: str) -> str:
    return pwd_context.hash(_bcrypt_safe(password))

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(_bcrypt_safe(password), hashed)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return username
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

# ---------------- AUTH ----------------
@app.post("/signup/")
def signup(username: str, password: str):
    db = SessionLocal()

    if db.query(User).filter(User.username == username).first():
        db.close()
        return {"success": False, "message": "User already exists"}

    user = User(username=username, password=hash_password(password))
    db.add(user)
    db.commit()
    db.close()

    return {"success": True, "message": "User created successfully"}

@app.post("/login/")
def login(username: str, password: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()

    if not user or not verify_password(password, user.password):
        return {"success": False, "message": "Invalid credentials"}

    token = create_access_token({"sub": username})
    return {"success": True, "access_token": token}

# ---------------- BACKGROUND JOB ----------------
def process_lecture_background(file_path: str, filename: str, username: str):
    try :
        # 1 - Transcribe (audio/video)
        transcription = transcribe(file_path)

        transcript_text = transcription["text"]
        transcript_segments = transcription["segments"]

        # 2 - Generate notes & quiz from TEXT ONLY
        notes = generate_notes(transcript_text)
        quiz = generate_quiz(transcript_text)

        # 3 - Export PDF
        pdf_path = f"data/outputs/{filename}.pdf"
        export_pdf(notes, pdf_path)

        duration_minutes = round(
            transcription["segments"][-1]["end"] / 60, 2
        )

        topics = notes.get("key_points",[])

        # 4 - Save to DB
        db = SessionLocal()
        history = LectureHistory(
            username=username,
            transcript=transcript_text,  # clean text
            notes=notes,
            segments=transcript_segments, # timestamped data
            duration_minutes=duration_minutes,
            topics=topics
        )

        db.add(history)
        db.commit()
        db.close()

    except Exception as e :
        print("Background process failed: ", e)

    finally :
        if os.path.exists(file_path) :
            os.remove(file_path)

# ---------------- DASHBOARD -------------
@app.get("/dashboard/")
def dashboard(current_user: str = Depends(get_current_user)):
    db = SessionLocal()
    lectures = db.query(LectureHistory)\
                 .filter(LectureHistory.username == current_user)\
                 .all()
    db.close()

    total_lectures = len(lectures)
    total_time = sum(l.duration_minutes for l in lectures)

    # Estimate time saved (manual notes ≈ 2x lecture time)
    time_saved = round(total_time * 2 - total_time, 2)

    all_topics = []
    for l in lectures:
        all_topics.extend(l.topics or [])

    topic_freq = {t: all_topics.count(t) for t in set(all_topics)}

    return {
        "lectures_processed": total_lectures,
        "total_learning_time_minutes": round(total_time, 2),
        "estimated_time_saved_minutes": time_saved,
        "topics_covered": topic_freq
    }

# ---------------- SEARCH ----------------
@app.get("/search/")
def search_lectures(
    query: str,
    current_user: str = Depends(get_current_user)
):
    db = SessionLocal()
    lectures = db.query(LectureHistory)\
                 .filter(
                     LectureHistory.username == current_user,
                     LectureHistory.transcript.contains(query)
                 ).all()
    db.close()

    results = []

    for l in lectures:
        matches = [
            s["text"] for s in l.segments
            if query.lower() in s["text"].lower()
        ]

        results.append({
            "lecture_id": l.id,
            "matches": matches[:5]
        })

    return results

# ---------------- PROCESS ----------------
@app.post("/process/")
async def process_file(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    current_user: str = Depends(get_current_user)
):
    file_path = f"data/audio/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(
        process_lecture_background,
        file_path,
        file.filename,
        current_user
    )

    return {
        "success": True,
        "message": "Lecture processing started in background"
    }

# ---------------- HISTORY ----------------
@app.get("/history/")
def get_history(current_user: str = Depends(get_current_user)):
    db = SessionLocal()
    lectures = db.query(LectureHistory).filter(
        LectureHistory.username == current_user
    ).all()
    db.close()
    return lectures
