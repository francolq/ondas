import sys
import librosa
import librosa.display
import matplotlib.pyplot as plt


def main():
    if len(sys.argv) < 2:
        print("Usage: python plot_waveform.py <input.wav> [output.png]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    y, sr = librosa.load(input_file)

    plt.figure(figsize=(10, 4))
    librosa.display.waveshow(y, sr=sr)
    plt.title(f"Waveform: {input_file}")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")

    if output_file:
        plt.savefig(output_file)
        print(f"Saved waveform to {output_file}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
