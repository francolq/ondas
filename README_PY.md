# WAV Utilities - Python Scripts

A collection of Python scripts for working with WAV audio files.

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv ondas
source ondas/bin/activate
pip install librosa matplotlib soundfile numpy sounddevice textual textual-slider
```

## Scripts

### sine.py
Generates a sine wave WAV file.

**Run:**
```bash
python sine.py
```
Outputs: `sine.wav` (440 Hz, 1 second, 16-bit mono, 44.1 kHz)

**With custom parameters:**
```bash
python -c "import sine; sine.create_sine_wav('440Hz.wav', frequency=440, duration=2.0)"
```

### sine_stream.py
Plays a sine wave in real-time using sounddevice.

**Run:**
```bash
python sine_stream.py
```
Press Enter to stop.

### wave_app.py
Interactive TUI app for real-time sine wave synthesis with amplitude and frequency sliders.

**Run:**
```bash
python wave_app.py
```
Use sliders to adjust amplitude (0-100%) and frequency (20-2000 Hz). Press Ctrl+C to quit.

### plot_waveform.py
Plots the waveform of a WAV file using librosa and matplotlib.

**Run:**
```bash
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
python plot_spectrogram.py <input.wav> [output.png]
```

Example:
```bash
python plot_spectrogram.py sine.wav sine_spectrogram.png
```

### bpm.py
Calculates the BPM of a WAV file using librosa.

**Run:**
```bash
python bpm.py <input.wav>
```

Example:
```bash
python bpm.py sine.wav
```

## Dependencies

- Python 3
- librosa
- matplotlib
- soundfile
- numpy
- sounddevice
- textual
- textual-slider
