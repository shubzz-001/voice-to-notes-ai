FROM python:3.10-slim

# To Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# To Set workdir
WORKDIR /app

# To Copy requirements
COPY requirements.txt .

# To Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# source code Copying
COPY backend ./backend

# Exposing HF port
EXPOSE 7860

# To Start FastAPI
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
