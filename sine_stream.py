import numpy as np
import sounddevice as sd
import time

SAMPLE_RATE = 44100
amplitude = 0.5
frequency = 440

start_idx = 0

def audio_callback(outdata, frames, time, status):
    """
    Called repeatedly by sounddevice whenever the audio buffer needs more samples.
    
    Args:
        outdata: Audio output buffer (shape: [frames, channels])
        frames: Number of audio frames to generate
        time: Time info (unused here)
        status: Audio error status (if any)
    """
    # Print any audio errors (e.g., underrun)
    if status:
        print(status)
    
    global start_idx
    
    # Create time array for current chunk:
    # - start_idx: total samples played so far (tracks wave phase)
    # - np.arange(frames): 0, 1, 2, ... up to frames-1
    # - Shape before: (frames,) - 1D array
    t = (start_idx + np.arange(frames)) / SAMPLE_RATE
    
    # Reshape to column vector for audio output
    # Shape after: (frames, 1) - required because outdata has shape (frames, channels)
    t = t.reshape(-1, 1)
    
    # Generate sine wave:
    # - 2 * np.pi * frequency * t: angular frequency formula
    # - np.sin(): computes sine for each sample
    # - amplitude: scales the wave (0.0 = silent, 1.0 = max volume)
    outdata[:] = amplitude * np.sin(2 * np.pi * frequency * t)
    
    # Increment counter to maintain phase continuity in next callback
    start_idx += frames


with sd.OutputStream(channels=1, samplerate=SAMPLE_RATE, callback=audio_callback):
    print("Playing sine wave... Press return to stop.")
    input()
