import wave
import numpy as np

def load_waveform(path, bars=2000):
    wf = wave.open(path, "rb")
    frames = wf.readframes(wf.getnframes())
    samples = np.frombuffer(frames, dtype=np.int16)

    samples = np.abs(samples)
    chunk = len(samples) // bars
    waveform = [
        samples[i*chunk:(i+1)*chunk].mean()
        for i in range(bars)
    ]

    duration = wf.getnframes() / wf.getframerate()
    wf.close()
    return waveform, duration
