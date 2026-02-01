import subprocess, json

def resolve_audio(video_id):
    try:
        cmd = [
            "yt-dlp",
            "-f", "bestaudio",
            "-j",
            "--quiet",
            f"https://music.youtube.com/watch?v={video_id}"
        ]
        data = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        return json.loads(data).get("url")
    except Exception:
        return None
