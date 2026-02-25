import struct
import math
import sys

def create_sine_wav(filename="sine.wav", frequency=440.0, duration=1.0,
                    sample_rate=44100, bits_per_sample=16, num_channels=1):
    num_samples = int(sample_rate * duration)
    data_size = num_samples * num_channels * (bits_per_sample // 8)
    file_size = 36 + data_size

    with open(filename, "wb") as f:
        f.write(b"RIFF")
        f.write(struct.pack("<I", file_size))
        f.write(b"WAVE")
        f.write(b"fmt ")
        f.write(struct.pack("<I", 16))
        f.write(struct.pack("<H", 1))
        f.write(struct.pack("<H", num_channels))
        f.write(struct.pack("<I", sample_rate))
        f.write(struct.pack("<I", sample_rate * num_channels * (bits_per_sample // 8)))
        f.write(struct.pack("<H", num_channels * (bits_per_sample // 8)))
        f.write(struct.pack("<H", bits_per_sample))
        f.write(b"data")
        f.write(struct.pack("<I", data_size))

        amplitude = 16000
        for i in range(num_samples):
            sample = amplitude * math.sin(2.0 * math.pi * frequency * i / sample_rate)
            s = int(sample)
            f.write(struct.pack("<h", s))

    print(f"Created {filename}: {int(frequency)} Hz, {duration:.1f} seconds")

if __name__ == "__main__":
    create_sine_wav()
