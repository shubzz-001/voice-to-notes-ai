import re
from typing import Optional, Dict
import subprocess
import os
import uuid
import sys


def extract_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from various URL formats"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def check_ytdlp_installed() -> bool:
    """Check if yt-dlp is installed and accessible"""
    try:
        result = subprocess.run(
            ["yt-dlp", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def download_youtube_audio(video_url: str, output_dir: str = "/data/youtube") -> Dict:
    """
    Download YouTube video audio using yt-dlp
    Returns dict with audio path and video info
    """
    try:
        # Check if yt-dlp is installed
        if not check_ytdlp_installed():
            raise Exception("yt-dlp is not installed. Please install it: pip install yt-dlp")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        video_id = extract_video_id(video_url)
        if not video_id:
            raise ValueError("Invalid YouTube URL. Please use format: youtube.com/watch?v=... or youtu.be/...")

        # Use a simpler filename
        output_template = os.path.join(output_dir, f"{video_id}.%(ext)s")

        print(f"Downloading YouTube video: {video_id}")
        print(f"Output directory: {output_dir}")

        # Download audio with yt-dlp
        command = [
            "yt-dlp",
            "--no-playlist",  # Don't download playlists
            "--extract-audio",
            "--audio-format", "wav",
            "--audio-quality", "0",
            "--output", output_template,
            "--no-warnings",
            "--no-check-certificate",  # Sometimes needed for corporate networks
            video_url
        ]

        print(f"Running command: {' '.join(command)}")

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
            cwd=output_dir  # Run in output directory
        )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            print(f"yt-dlp error: {error_msg}")
            raise Exception(f"Download failed: {error_msg[:200]}")

        # Find the downloaded file
        downloaded_files = [f for f in os.listdir(output_dir) if f.startswith(video_id)]

        if not downloaded_files:
            raise Exception(f"Download completed but file not found in {output_dir}")

        audio_path = os.path.join(output_dir, downloaded_files[0])
        print(f"Successfully downloaded: {audio_path}")

        return {
            "success": True,
            "audio_path": audio_path,
            "video_id": video_id
        }

    except subprocess.TimeoutExpired:
        raise Exception("Download timeout - video might be too long (max 10 minutes recommended)")
    except FileNotFoundError:
        raise Exception("yt-dlp command not found. Install it with: pip install yt-dlp")
    except Exception as e:
        print(f"YouTube download error: {str(e)}")
        raise Exception(f"YouTube download failed: {str(e)}")


def get_youtube_metadata(video_url: str) -> Dict:
    """
    Get YouTube video metadata (title, duration, thumbnail, etc.)
    """
    try:
        if not check_ytdlp_installed():
            return {
                "title": "Unknown (yt-dlp not installed)",
                "duration": 0,
                "uploader": "Unknown",
                "thumbnail": None,
                "video_id": extract_video_id(video_url)
            }

        command = [
            "yt-dlp",
            "--print", "%(title)s",
            "--print", "%(duration)s",
            "--print", "%(uploader)s",
            "--print", "%(thumbnail)s",
            "--no-warnings",
            video_url
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            video_id = extract_video_id(video_url)
            return {
                "title": lines[0] if len(lines) > 0 else "Unknown",
                "duration": int(lines[1]) if len(lines) > 1 and lines[1].isdigit() else 0,
                "uploader": lines[2] if len(lines) > 2 else "Unknown",
                "thumbnail": lines[3] if len(lines) > 3 else f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                "video_id": video_id
            }

        video_id = extract_video_id(video_url)
        return {
            "title": "Unknown",
            "duration": 0,
            "uploader": "Unknown",
            "thumbnail": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg" if video_id else None,
            "video_id": video_id
        }

    except Exception as e:
        print(f"Error getting metadata: {e}")
        video_id = extract_video_id(video_url)
        return {
            "title": "Unknown",
            "duration": 0,
            "uploader": "Unknown",
            "thumbnail": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg" if video_id else None,
            "video_id": video_id
        }


def summarize_youtube_video(video_url: str) -> Dict:
    """
    Complete workflow: Download YouTube video and prepare for transcription
    """
    try:
        print(f"Processing YouTube URL: {video_url}")

        # Validate URL first
        video_id = extract_video_id(video_url)
        if not video_id:
            return {
                "success": False,
                "error": "Invalid YouTube URL format"
            }

        # Get metadata first (faster, good for validation)
        print("Fetching video metadata...")
        metadata = get_youtube_metadata(video_url)

        # Download audio
        print("Downloading audio...")
        download_result = download_youtube_audio(video_url)

        if not download_result.get("success"):
            return {
                "success": False,
                "error": "Failed to download video"
            }

        return {
            "success": True,
            "audio_path": download_result["audio_path"],
            "video_id": download_result["video_id"],
            "metadata": metadata
        }

    except Exception as e:
        error_message = str(e)
        print(f"YouTube processing error: {error_message}")
        return {
            "success": False,
            "error": error_message
        }


# Diagnostic function
def diagnose_youtube_setup():
    """
    Check if YouTube downloading is properly set up
    Returns dict with status of each requirement
    """
    diagnostics = {
        "yt-dlp": False,
        "ffmpeg": False,
        "write_permission": False
    }

    # Check yt-dlp
    try:
        result = subprocess.run(["yt-dlp", "--version"], capture_output=True, timeout=5)
        diagnostics["yt-dlp"] = result.returncode == 0
    except:
        pass

    # Check ffmpeg
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        diagnostics["ffmpeg"] = result.returncode == 0
    except:
        pass

    # Check write permission
    try:
        test_dir = "/data/youtube"
        os.makedirs(test_dir, exist_ok=True)
        test_file = os.path.join(test_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        diagnostics["write_permission"] = True
    except:
        pass

    return diagnostics