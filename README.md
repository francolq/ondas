# WAV Utilities

A collection of C programs for working with WAV audio files.

## Programs

### sine.c
Generates a sine wave WAV file.

**Compile & Run:**
```bash
gcc sine.c -o sine -lm
./sine
```
Outputs: `sine.wav` (440 Hz, 1 second, 16-bit mono, 44.1 kHz)

### sine.py
Python version of sine wave generator (requires Python 3).

**Run:**
```bash
python3 sine.py
```
Outputs: `sine.wav` (440 Hz, 1 second, 16-bit mono, 44.1 kHz)

**With custom parameters:**
```bash
python3 -c "import sine; sine.create_sine_wav('440Hz.wav', frequency=440, duration=2.0)"
```

### sine_stereo.c
Generates a stereo sine wave WAV file with panning from left to right channel.

**Compile & Run:**
```bash
gcc sine_stereo.c -o sine_stereo -lm
./sine_stereo
```
Outputs: `sine_stereo.wav` (440 Hz, 1 second, 16-bit stereo, 44.1 kHz)

### sawtooth.c
Generates a sawtooth wave WAV file.

**Compile & Run:**
```bash
gcc sawtooth.c -o sawtooth -lm
./sawtooth
```
Outputs: `sawtooth.wav` (440 Hz, 1 second, 16-bit mono, 44.1 kHz)

### square.c
Generates a square wave WAV file.

**Compile & Run:**
```bash
gcc square.c -o square -lm
./square
```
Outputs: `square.wav` (440 Hz, 1 second, 16-bit mono, 44.1 kHz)

### wavinfo.c
Prints information about a WAV file.

**Compile & Run:**
```bash
gcc wavinfo.c -o wavinfo
./wavinfo <file.wav>
```

Example:
```bash
./wavinfo sine.wav
```

### wavplot.c
Plots a WAV file as a PNG waveform image.

**Compile & Run:**
```bash
gcc wavplot.c -o wavplot -lm
./wavplot <input.wav> <output.png> [width] [height]
```

Example:
```bash
./wavplot sine.wav sine_plot.png
./wavplot sine.wav sine_plot_large.png 1200 300
```

### plot_waveform.py
Plots the waveform of a WAV file using librosa and matplotlib.

**Install dependencies:**
```bash
python3 -m venv ondas
source ondas/bin/activate
pip install librosa matplotlib
```

**Run:**
```bash
source ondas/bin/activate
python plot_waveform.py <input.wav> [output.png]
```

Example:
```bash
python plot_waveform.py sine.wav sine_waveform.png
```

### plot_spectrogram.py
Plots the spectrogram of a WAV file using librosa and matplotlib.

**Run:**
```bash
source ondas/bin/activate
python plot_spectrogram.py <input.wav> [output.png]
```

Example:
```bash
python plot_spectrogram.py sine.wav sine_spectrogram.png
```

## Dependencies

- `wavplot.c` requires `stb_image_write.h` (included)
- Standard C library (`libm` for math functions)
- Python 3 (for Python scripts)
- Python virtual environment `ondas` with librosa and matplotlib (for plotting scripts)
