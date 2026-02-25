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

## Dependencies

- `wavplot.c` requires `stb_image_write.h` (included)
- Standard C library (`libm` for math functions)
