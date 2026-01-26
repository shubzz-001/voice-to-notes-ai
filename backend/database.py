import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Get the project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Create data directory if it doesn't exist
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Database path - relative to project root
DB_PATH = os.path.join(DATA_DIR, "lecture_ai.db")

# SQLite URL with proper formatting (3 slashes for relative path)
DATABASE_URL = f"sqlite:///{DB_PATH}"

print(f"Database will be created at: {DB_PATH}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()