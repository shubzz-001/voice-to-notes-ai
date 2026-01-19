import os
import subprocess
import uuid

def extract_audio_from_video(video_path: str) -> str:
    """
    Extract audio from video using ffmpeg.
    Returns path to extracted WAV audio.
    """

    output_audio = f"data/audio/{uuid.uuid4().hex}.wav"

    command = [
        "ffmpeg",
        "-y",                   # overwrite
        "-i", video_path,
        "-vn",                  # no video
        "-ac", "1",             # mono
        "-ar", "16000",          # 16kHz (Whisper optimal)
        output_audio
    ]

    subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )

    return output_audio
