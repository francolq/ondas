import sys
import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt


def main():
    if len(sys.argv) < 2:
        print("Usage: python plot_spectrogram.py <input.wav> [output.png]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    y, sr = librosa.load(input_file)

    D = librosa.stft(y)
    S_db = librosa.amplitude_to_db(abs(D), ref=np.max)

    plt.figure(figsize=(10, 6))
    librosa.display.specshow(S_db, sr=sr, x_axis="time", y_axis="log")
    plt.colorbar(label="Amplitude (dB)")
    plt.title(f"Spectrogram: {input_file}")
    plt.xlabel("Time (s)")
    plt.ylabel("Frequency (Hz)")

    if output_file:
        plt.savefig(output_file)
        print(f"Saved spectrogram to {output_file}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
