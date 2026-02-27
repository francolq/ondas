CC = gcc
CFLAGS = -Wall -Wextra -pedantic -g
LDFLAGS = -lm

SRCS = sine.c sine_stereo.c sawtooth.c square.c wavinfo.c wavplot.c
TARGETS = sine sine_stereo sawtooth square wavinfo wavplot

.PHONY: all clean

all: $(TARGETS)

sine: sine.c
	$(CC) $(CFLAGS) sine.c -o sine $(LDFLAGS)

sine_stereo: sine_stereo.c
	$(CC) $(CFLAGS) sine_stereo.c -o sine_stereo $(LDFLAGS)

sawtooth: sawtooth.c
	$(CC) $(CFLAGS) sawtooth.c -o sawtooth $(LDFLAGS)

square: square.c
	$(CC) $(CFLAGS) square.c -o square $(LDFLAGS)

wavinfo: wavinfo.c
	$(CC) $(CFLAGS) wavinfo.c -o wavinfo

wavplot: wavplot.c
	$(CC) $(CFLAGS) wavplot.c -o wavplot $(LDFLAGS)

clean:
	rm -f $(TARGETS)
