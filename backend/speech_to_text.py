import whisper
import subprocess
import os
import uuid
from pydub import AudioSegment

BASE_DATA = "data"
AUDIO_DIR = f"{BASE_DATA}/audio"
TRANSCRIPT_DIR = f"{BASE_DATA}/transcripts"

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)

model = whisper.load_model("small")


def extract_audio_from_video(video_path: str) -> str:
    audio_path = f"{AUDIO_DIR}/{uuid.uuid4().hex}.wav"

    command = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-map", "a:0",
        "-ac", "1",
        "-ar", "16000",
        "-vn",
        "-loglevel", "error",
        audio_path
    ]
    subprocess.run(command, check=True)
    return audio_path


def split_audio(audio_path, chunk_length_ms=10 * 60 * 1000):
    audio = AudioSegment.from_file(audio_path)
    chunks = []

    for i in range(0, len(audio), chunk_length_ms):
        chunk_path = f"{audio_path}_chunk_{i}.wav"
        audio[i:i+chunk_length_ms].export(chunk_path, format="wav")
        chunks.append(chunk_path)

    return chunks


def transcribe(file_path: str):
    ext = file_path.split(".")[-1].lower()
    temp_audio = None

    if ext in ["mp4", "mkv", "avi", "mov", "webm"]:
        temp_audio = extract_audio_from_video(file_path)
        audio_path = temp_audio
    else:
        audio_path = file_path

    chunks = split_audio(audio_path)

    full_text = []
    segments = []
    offset = 0.0

    for chunk in chunks:
        result = model.transcribe(chunk, fp16=False, language="en")
        full_text.append(result["text"])

        for seg in result["segments"]:
            segments.append({
                "start": round(seg["start"] + offset, 2),
                "end": round(seg["end"] + offset, 2),
                "text": seg["text"]
            })

        duration = AudioSegment.from_file(chunk)
        offset += len(duration) / 1000
        os.remove(chunk)

    if temp_audio:
        os.remove(temp_audio)

    transcript_text = " ".join(full_text)

    transcript_path = f"{TRANSCRIPT_DIR}/{uuid.uuid4().hex}.txt"
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(transcript_text)

    return {
        "text": transcript_text,
        "segments": segments,
        "transcript_path": transcript_path
    }
