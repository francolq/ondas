# AGENTS.md - WAV Utilities Project

## Project Overview

Mixed C and Python project for WAV audio generation and analysis. Contains C programs for wave generation (sine, sawtooth, square) and utilities (wavinfo, wavplot), plus Python scripts for advanced audio processing.

## Project Structure

```
wav/
├── *.c                # C programs (sine, sawtooth, square, wavinfo, wavplot)
├── *.py               # Python scripts (sine.py, wave_app.py, midi_input.py, etc.)
├── ondas/             # Python virtual environment
├── Makefile           # C build automation
└── AGENTS.md          # This file
```

## Build Commands (C)

### Using Makefile (Recommended)

```bash
make              # Build all C programs
make sine         # Build specific program
make sawtooth
make square
make wavinfo
make wavplot
make clean        # Remove build artifacts
```

### Manual Compilation

```bash
# With math library (-lm)
gcc -Wall -Wextra -pedantic -g sine.c -o sine -lm
gcc -Wall -Wextra -pedantic -g sawtooth.c -o sawtooth -lm
gcc -Wall -Wextra -pedantic -g square.c -o square -lm

# Without math library
gcc -Wall -Wextra -pedantic -g wavinfo.c -o wavinfo

# With stb_image_write (wavplot)
gcc -Wall -Wextra -pedantic -g wavplot.c -o wavplot -lm
```

### Compiler Flags

- `-Wall -Wextra -pedantic`: Enable strict warnings (required)
- `-g`: Debug symbols
- `-lm`: Math library (for sin, cos, M_PI, fmod)

## Build Commands (Python)

```bash
# Setup virtual environment
python3 -m venv ondas
source ondas/bin/activate
pip install librosa matplotlib soundfile numpy sounddevice textual textual-slider mido python-rtmidi

# Run Python scripts
python sine.py
python wave_app.py
python midi_input.py
```

## Running Programs

### C Programs

```bash
./sine              # Generates sine.wav (440 Hz, 1 second)
./sawtooth          # Generates sawtooth.wav
./square            # Generates square.wav
./wavinfo <file>    # Display WAV metadata
./wavplot in.wav out.png [width height]
```

### Python Programs

```bash
python sine.py [freq] [duration]     # Generate sine.wav
python wave_app.py                    # Interactive TUI sine generator
python midi_input.py                  # MIDI keyboard input
python plot_waveform.py <in.wav> [out.png]
python plot_spectrogram.py <in.wav> [out.png]
python bpm.py <in.wav>                # Calculate BPM
```

## Testing

### Manual Testing Approach

```bash
# Build and test C programs
make sine && ./sine && ./wavinfo sine.wav

# Memory leak checking
valgrind --leak-check=full ./sine

# Verify WAV file integrity
./wavinfo output.wav
file output.wav
```

### Python Testing

```bash
# Test sine generation
python sine.py && python -c "import sine; sine.create_sine_wav()"

# Test with audio playback (if available)
aplay sine.wav
```

## Code Style Guidelines

### C Style

**Formatting**
- 4 spaces indentation (no tabs)
- K&R braces (opening on same line)
- Line length: under 100 characters
- Single blank line between logical sections

**Naming Conventions**
- Types: PascalCase (`WavHeader`, `AudioConfig`)
- Variables: camelCase (`sampleRate`, `fileSize`, `numChannels`)
- Constants: UPPER_CASE (`MAX_SAMPLES`, `DEFAULT_FREQUENCY`)
- Functions: snake_case (`write_wav_header`, `read_wav_file`)

**Imports (alphabetical)**
```c
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
```

**Types**
- `int`: Most integers
- `short`: 16-bit audio samples
- `double`: Floating-point calculations
- Fixed-width: `int32_t`, `uint16_t` from `<stdint.h>`

**Error Handling**
```c
FILE *fp = fopen("file.wav", "rb");
if (!fp) {
    perror("Failed to open file");
    return 1;
}
```

**Code Organization**
1. Includes
2. Type definitions
3. Function prototypes
4. Global constants
5. Main and helper functions

### Python Style

**Formatting**
- 4 spaces indentation (PEP 8)
- Line length: 100 characters

**Naming Conventions**
- Functions/classes: snake_case
- Constants: UPPER_CASE
- Variables: snake_case

**Imports (alphabetical)**
```python
import math
import struct
import sys
```

**Error Handling**
```python
if not os.path.exists(filename):
    print(f"Error: {filename} not found", file=sys.stderr)
    return 1
```

## WAV File Format

- Binary mode (`"rb"`, `"wb"`)
- Little-endian byte ordering
- Structure: RIFF header → fmt chunk → data chunk
- 16-bit signed samples for audio data
- Standard sample rates: 44100 Hz, 48000 Hz

## Best Practices

- Always close file handles (`fclose()`, `with` statements)
- Check all file operations for NULL/None
- Return non-zero exit codes on failure
- Use `const` for read-only variables
- Prefer stack over heap allocation
