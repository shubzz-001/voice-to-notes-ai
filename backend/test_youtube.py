"""
YouTube Setup Diagnostic Script
Run this to check if YouTube downloading is working
"""

import subprocess
import sys
import os


def check_command(command, name):
    """Check if a command is available"""
    try:
        result = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✅ {name} is installed: {version}")
            return True
        else:
            print(f"❌ {name} command failed")
            return False
    except FileNotFoundError:
        print(f"❌ {name} not found")
        return False
    except Exception as e:
        print(f"❌ {name} error: {e}")
        return False


def test_youtube_download():
    """Test actual YouTube download"""
    print("\n🧪 Testing YouTube download...")

    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # Short "Me at the zoo" video

    try:
        # Just get metadata, don't download
        result = subprocess.run(
            ["yt-dlp", "--print", "%(title)s", test_url],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            title = result.stdout.strip()
            print(f"✅ Successfully accessed YouTube: '{title}'")
            return True
        else:
            print(f"❌ YouTube access failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ YouTube test failed: {e}")
        return False


def check_write_permissions():
    """Check if we can write to data directory"""
    print("\n📁 Checking write permissions...")

    try:
        test_dir = "./data/youtube"
        os.makedirs(test_dir, exist_ok=True)
        test_file = os.path.join(test_dir, "test.txt")

        with open(test_file, "w") as f:
            f.write("test")

        os.remove(test_file)
        print(f"✅ Can write to {test_dir}")
        return True
    except Exception as e:
        print(f"❌ Cannot write to data directory: {e}")
        return False


def main():
    print("🔍 YouTube Download Diagnostics\n")
    print("=" * 50)

    results = {
        "python": True,  # If we're running, Python works
        "yt-dlp": check_command("yt-dlp", "yt-dlp"),
        "ffmpeg": check_command("ffmpeg", "FFmpeg"),
        "permissions": check_write_permissions(),
        "youtube_access": False
    }

    print(f"\n✅ Python {sys.version.split()[0]}")

    if results["yt-dlp"]:
        results["youtube_access"] = test_youtube_download()

    print("\n" + "=" * 50)
    print("\n📊 Results Summary:\n")

    for component, status in results.items():
        symbol = "✅" if status else "❌"
        print(f"{symbol} {component.upper()}: {'OK' if status else 'FAILED'}")

    print("\n" + "=" * 50)

    if not results["yt-dlp"]:
        print("\n🔧 Fix: Install yt-dlp")
        print("   pip install yt-dlp")

    if not results["ffmpeg"]:
        print("\n🔧 Fix: Install FFmpeg")
        print("   Windows: https://ffmpeg.org/download.html")
        print("   Mac: brew install ffmpeg")
        print("   Linux: sudo apt install ffmpeg")

    if not results["permissions"]:
        print("\n🔧 Fix: Check directory permissions")
        print("   Make sure ./data/youtube directory is writable")

    if all(results.values()):
        print("\n🎉 All checks passed! YouTube downloading should work!")
    else:
        print("\n⚠️  Some issues found. Please fix them and try again.")

    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)