import whisper
from pydub import AudioSegment
import subprocess
import os
import uuid

# Load Whisper model once
model = whisper.load_model("base")


def extract_audio_from_video(video_path: str) -> str:
    """
    Extract audio from video file using FFmpeg
    """
    audio_path = f"data/audio/{uuid.uuid4()}.wav"

    command = [
        "ffmpeg",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        audio_path,
        "-y"
    ]

    subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return audio_path


def split_audio(audio_path: str, chunk_length_ms=5 * 60 * 1000):
    """
    Split audio into WAV chunks (5 minutes default)
    """
    audio = AudioSegment.from_file(audio_path)
    chunks = []

    for i in range(0, len(audio), chunk_length_ms):
        chunk = audio[i:i + chunk_length_ms]
        chunk_path = f"{audio_path}_chunk_{i // chunk_length_ms}.wav"
        chunk.export(chunk_path, format="wav")
        chunks.append(chunk_path)

    return chunks



# Main Transcription Function

def transcribe(file_path: str) -> str:
    """
    Transcribe audio OR video file using Whisper
    """
    ext = file_path.split(".")[-1].lower()
    temp_audio = None

    # If video, extract audio first
    if ext in ["mp4", "mkv", "avi", "mov"]:
        temp_audio = extract_audio_from_video(file_path)
        audio_path = temp_audio
    else:
        audio_path = file_path

    chunks = split_audio(audio_path)
    full_text = ""

    for chunk in chunks:
        result = model.transcribe(chunk, fp16=False)
        full_text += result["text"] + " "
        os.remove(chunk)

    # Cleanup extracted audio
    if temp_audio and os.path.exists(temp_audio):
        os.remove(temp_audio)

    return full_text.strip()
