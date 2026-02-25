import sys
import librosa


def main():
    if len(sys.argv) < 2:
        print("Usage: python bpm.py <input.wav>")
        sys.exit(1)

    input_file = sys.argv[1]

    y, sr = librosa.load(input_file)

    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)

    print(f"BPM: {tempo:.2f}")
    print(f"Detected beats: {len(beats)}")


if __name__ == "__main__":
    main()
