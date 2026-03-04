import sys
import sounddevice as sd
import soundfile as sf
import numpy as np


def sample_stream(input_file, volume=1.0):
    sample, sr = sf.read(input_file)

    if len(sample.shape) > 1:
        sample = sample.mean(axis=1)

    sample = sample * volume

    idx = 0

    def callback(outdata, frames, time_info, status):
        nonlocal idx

        if status:
            print(status)

        remaining = len(sample) - idx

        if remaining >= frames:
            outdata[:] = sample[idx:idx + frames].reshape(-1, 1)
            idx += frames
        else:
            outdata[:remaining] = sample[idx:].reshape(-1, 1)
            outdata[remaining:] = sample[:frames - remaining].reshape(-1, 1)
            idx = frames - remaining

    print(f"Looping: {input_file}. Press Enter to stop.")

    stream = sd.OutputStream(channels=1, samplerate=sr, callback=callback)
    stream.start()

    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass

    stream.close()
    print("Stopped.")


def main():
    if len(sys.argv) < 2:
        print("Usage: python sample_stream.py <sample.wav> [volume]")
        sys.exit(1)

    input_file = sys.argv[1]
    volume = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0

    sample_stream(input_file, volume)


if __name__ == "__main__":
    main()
