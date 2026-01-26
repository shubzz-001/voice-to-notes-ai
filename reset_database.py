"""
Reset Database Script
Save this file in your project root directory and run: python reset_database.py
"""

import os
from backend.database import engine
from backend.models import Base

# Database file path
DB_PATH = "./data/lecture_ai.db"

# Delete old database if it exists
if os.path.exists(DB_PATH):
    print(f"Deleting old database at {DB_PATH}...")
    os.remove(DB_PATH)
    print("✓ Old database deleted")
else:
    print(f"No existing database found at {DB_PATH}")

# Create data directory if it doesn't exist
os.makedirs("./data", exist_ok=True)

# Create new database with updated schema
print("Creating new database with updated schema...")
Base.metadata.create_all(bind=engine)
print("✓ Database initialized and tables created successfully!")
print("\nYou can now:")
print("1. Start the backend: uvicorn backend.main:app --reload")
print("2. Start the frontend: streamlit run frontend/app.py")
print("3. Sign up with a new account")