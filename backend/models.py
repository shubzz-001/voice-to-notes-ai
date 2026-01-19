from sqlalchemy import Column, Integer, String, Text, JSON, Float
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String)

class LectureHistory(Base):
    __tablename__ = "lectures"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)

    transcript = Column(Text)
    notes = Column(Text)

    segments = Column(JSON)

    duration_minutes = Column(Float)
    topics = Column(JSON)