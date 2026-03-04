# AGENTS.md - WAV Utilities Project

## Project Overview

This is a C project containing WAV audio utilities (sine, sawtooth, square wave generators, wavinfo, wavplot). Each program is a standalone C file that compiles to an executable.

## Project Structure

```
wav/
├── sine.c           # Sine wave generator
├── sine_stereo.c   # Stereo sine wave generator
├── sawtooth.c      # Sawtooth wave generator
├── square.c        # Square wave generator
├── wavinfo.c       # WAV file info utility
├── wavplot.c       # WAV waveform plotter (requires libgd)
├── Makefile        # Build automation
└── AGENTS.md       # This file
```

## Build Commands

### Using Makefile (Recommended)

```bash
# Build all programs
make

# Build a specific program
make sine
make sawtooth
make square
make wavinfo
make wavplot

# Clean build artifacts
make clean
```

### Manual Compilation

```bash
# Programs requiring math library (-lm)
gcc -Wall -Wextra -pedantic -g sine.c -o sine -lm
gcc -Wall -Wextra -pedantic -g sine_stereo.c -o sine_stereo -lm
gcc -Wall -Wextra -pedantic -g sawtooth.c -o sawtooth -lm
gcc -Wall -Wextra -pedantic -g square.c -o square -lm
gcc -Wall -Wextra -pedantic -g wavplot.c -o wavplot -lm

# Programs without math library
gcc -Wall -Wextra -pedantic -g wavinfo.c -o wavinfo
```

### Compiler Flags

- `-Wall -Wextra -pedantic`: Enable strict warnings
- `-g`: Debug symbols
- `-lm`: Math library (required for sin, cos, M_PI)
- `-lgd`: Image library (for wavplot)

## Run Programs

```bash
./sine                    # Generates sine.wav (440 Hz, 1 second)
./sawtooth               # Generates sawtooth.wav
./square                # Generates square.wav
./wavinfo <file.wav>     # Display WAV file metadata
./wavplot <input.wav> <output.png> [width] [height]
```

## Testing

No formal test framework exists. Testing is manual:

1. Compile a program: `make <target>`
2. Run it and check output files
3. Verify WAV files: `./wavinfo output.wav`
4. Play audio with an audio player (e.g., `aplay`, `audacity`)
5. Check for memory leaks: `valgrind ./program`

### Running a Single Program for Testing

```bash
# Build and test sine wave
make sine && ./sine
./wavinfo sine.wav

# Build and test wavinfo
make wavinfo && ./wavinfo sine.wav
```

## Linting

No formal linter configured. Manually check for:

- Memory leaks (use `valgrind ./program`)
- Buffer overflows
- Proper file handle cleanup (`fclose()`)
- Uninitialized variables

## Code Style Guidelines

### Formatting

- **Indentation**: 4 spaces (no tabs)
- **Braces**: K&R style (opening brace on same line)
- **Line length**: Keep under 100 characters when practical
- **Blank lines**: Single blank line between logical sections

### Naming Conventions

- **Types**: PascalCase (e.g., `WavHeader`, `AudioConfig`)
- **Variables**: camelCase (e.g., `sampleRate`, `fileSize`, `numChannels`)
- **Constants**: UPPER_CASE with underscores (e.g., `MAX_SAMPLES`)
- **Functions**: snake_case (e.g., `write_wav_header`)

### Imports

Order includes alphabetically:
1. Standard C headers (`<stdio.h>`, `<stdlib.h>`, `<math.h>`, `<string.h>`)
2. System headers
3. Project-specific headers (none currently)

```c
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
```

### Types

- `int`: Most integer values
- `short`: 16-bit audio samples
- `double`: Floating-point audio calculations
- Fixed-width types from `<stdint.h>` when exact size matters (`int32_t`, `uint16_t`)

### Structures

```c
typedef struct {
    char riff[4];
    int file_size;
    char wave[4];
} WavHeader;
```

### Error Handling

- Check all file operations for NULL
- Use `perror()` for descriptive errors
- Return non-zero exit codes on failure
- Close file handles in all code paths

```c
FILE *fp = fopen("output.wav", "wb");
if (!fp) {
    perror("Failed to open file");
    return 1;
}
```

### Memory Management

- Always `fclose()` files after use
- Check `malloc()` return values for NULL
- Use `memset()` for zero-initialization

### Constants

Define as variables with descriptive names:
```c
double frequency = 440.0;
int sample_rate = 44100;
int bits_per_sample = 16;
int num_channels = 1;
```

### Code Organization

1. Includes
2. Type definitions
3. Function prototypes (if needed)
4. Global constants (if any)
5. Main and helper functions

### WAV File Handling

- Use binary mode (`"rb"`, `"wb"`)
- Write header before audio data
- Use little-endian byte ordering
- Calculate correct `data_size` and `file_size`

### Best Practices

- Use `const` for read-only variables
- Prefer stack over heap when possible
- Enable all warnings: `-Wall -Wextra -pedantic`
