# AGENTS.md - WAV Utilities Project

## Project Overview

This is a C project containing WAV audio utilities (sine, sawtooth, square wave generators, wavinfo, wavplot). Each program is a standalone C file that compiles to an executable.

## Build Commands

### Compile Individual Programs

```bash
# Hello World
gcc hello.c -o hello

# Sine wave generator (requires -lm for math library)
gcc sine.c -o sine -lm

# Stereo sine wave
gcc sine_stereo.c -o sine_stereo -lm

# Sawtooth wave
gcc sawtooth.c -o sawtooth -lm

# Square wave
gcc square.c -o square -lm

# WAV file info
gcc wavinfo.c -o wavinfo

# WAV waveform plotter (requires -lm)
gcc wavplot.c -o wavplot -lm
```

### Run Programs

```bash
./hello
./sine
./sawtooth
./square
./wavinfo <file.wav>
./wavplot <input.wav> <output.png> [width] [height]
```

### Testing

There is no formal test framework. Manual testing involves:
1. Compiling a program
2. Running it and checking output files
3. Verifying WAV files with `wavinfo` or checking output with an audio player

### Linting

No formal linter is configured. Code should be checked manually for:
- Memory leaks (use `valgrind` if available)
- Buffer overflows
- Proper file handle cleanup

## Code Style Guidelines

### Formatting

- **Indentation**: 4 spaces (no tabs)
- **Braces**: K&R style (opening brace on same line)
- **Line length**: Keep under 100 characters when practical
- **Blank lines**: Single blank line between logical sections

### Naming Conventions

- **Types**: PascalCase (e.g., `WavHeader`, `AudioConfig`)
- **Variables**: camelCase (e.g., `sampleRate`, `fileSize`, `numChannels`)
- **Constants**: Use uppercase with underscores (e.g., `MAX_SAMPLES`, `DEFAULT_FREQUENCY`)
- **Functions**: snake_case (e.g., `write_wav_header`, `calculate_sample`)

### Imports

Order includes:
1. Standard C library headers (`<stdio.h>`, `<stdlib.h>`, `<math.h>`, `<string.h>`)
2. Project-specific headers (if any)

```c
#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
```

### Types

- Use `int` for most integer values
- Use `short` for 16-bit audio samples
- Use `double` for floating-point audio calculations
- Use fixed-width types from `<stdint.h>` when exact size matters (`int32_t`, `uint16_t`)

### Structures

```c
typedef struct {
    char riff[4];
    int file_size;
    char wave[4];
    // ...
} WavHeader;
```

### Error Handling

- Check all file operations for NULL returns
- Use `perror()` for descriptive error messages
- Return non-zero exit codes on failure
- Close file handles in all code paths (including error paths)

```c
FILE *fp = fopen("output.wav", "wb");
if (!fp) {
    perror("Failed to open file");
    return 1;
}
```

### Memory Management

- Always `fclose()` files after use
- Use `malloc()`/`free()` for dynamic memory
- Check malloc return values for NULL
- Zero-initialize structures when needed with `memset()`

### Constants

Define numeric constants as variables with descriptive names:

```c
double frequency = 440.0;
int sample_rate = 44100;
int bits_per_sample = 16;
int num_channels = 1;
```

### Comments

- Keep comments brief and purposeful
- Explain *why*, not *what*
- Document function parameters and return values
- No excessive commenting on obvious code

### Code Organization

1. Includes
2. Type definitions
3. Function prototypes (if needed)
4. Global constants (if any)
5. Main function and helper functions

### WAV File Handling

- Always use binary mode (`"rb"`, `"wb"`) for WAV files
- Write header before audio data
- Use correct byte ordering for WAV format (little-endian)
- Calculate correct `data_size` and `file_size` fields

### Best Practices

- Compile with warnings enabled: `gcc -Wall -Wextra -pedantic`
- Enable debug symbols for development: `gcc -g`
- Example: `gcc -Wall -Wextra -g -o program program.c -lm`
- Use `const` for variables that shouldn't change
- Prefer stack allocation over heap when possible
