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
    transcript = transcribe(file_path)
    notes = generate_notes(transcript)
    quiz = generate_quiz(transcript)

    pdf_path = f"data/outputs/{filename}.pdf"
    export_pdf(notes, pdf_path)

    db = SessionLocal()
    history = LectureHistory(
        username=username,
        transcript=transcript,
        notes=notes
    )
    db.add(history)
    db.commit()
    db.close()

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
