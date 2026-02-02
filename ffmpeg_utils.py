import subprocess
import os

def extract_audio(video_path, out_wav="audio.wav"):
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn", "-ac", "1", "-ar", "44100",
        out_wav
    ], check=True)
    return out_wav

def export_clip(video, start, end, out_file):
    cmd = ["ffmpeg", "-y", "-ss", str(start), "-to", str(end), "-i", video]

    if out_file.endswith(".mp4"):
        cmd += ["-c", "copy", out_file]
    elif out_file.endswith(".mp3"):
        cmd += ["-vn", "-acodec", "libmp3lame", out_file]
    else:
        cmd += ["-vn", out_file]

    subprocess.run(cmd, check=True)
