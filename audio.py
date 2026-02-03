# audio.py
import subprocess
import numpy as np
import wave
from pathlib import Path

BASE_DIR = Path.cwd()
CLIPS_DIR = BASE_DIR / "clips"
CLIPS_DIR.mkdir(exist_ok=True)

def extract_audio(input_path: Path) -> Path:
    out = input_path.with_suffix(".extracted.wav")

    if out.exists():
        return out

    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-vn",
        "-ac", "1",
        "-ar", "44100",
        str(out)
    ], check=True)

    return out


def load_waveform(path, samples=2000):
    with wave.open(str(path), "rb") as wf:
        frames = wf.readframes(wf.getnframes())
        audio = np.frombuffer(frames, dtype=np.int16)

        if wf.getnchannels() == 2:
            audio = audio[::2]

        audio = np.abs(audio)

        step = max(1, len(audio) // samples)
        waveform = audio[::step][:samples]

    return waveform

_clip_counter = 1

def clip_audio(input_path, start_ms, end_ms):
    global _clip_counter

    input_path = Path(input_path)

    out_path = CLIPS_DIR / f"audio_{_clip_counter}.wav"
    _clip_counter += 1

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),
        "-ss", f"{start_ms/1000:.3f}",
        "-to", f"{end_ms/1000:.3f}",
        str(out_path)
    ]

    subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )

    return out_path