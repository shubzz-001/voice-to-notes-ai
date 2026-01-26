from sqlalchemy import Column, Integer, String, Text, JSON, Float, DateTime
from datetime import datetime
from backend.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    # Removed email and created_at to match existing database


class LectureHistory(Base):
    __tablename__ = "lectures"
    id = Column(Integer, primary_key=True)
    username = Column(String, index=True)

    # Source information
    source_type = Column(String, default="upload")  # upload, youtube, url
    source_url = Column(String, nullable=True)  # For YouTube or web URLs
    title = Column(String, nullable=True)

    # Processing results
    transcript = Column(Text)
    notes = Column(Text)
    summary = Column(Text)  # Short summary
    segments = Column(JSON)  # Transcript segments with timestamps
    topics = Column(JSON)  # Extracted topics
    flashcards = Column(JSON)  # Generated flashcards
    key_moments = Column(JSON)  # Timestamped highlights

    # Metadata
    duration_minutes = Column(Float)
    language = Column(String, default="en")
    status = Column(String, default="processing")
    created_at = Column(DateTime, default=datetime.utcnow)