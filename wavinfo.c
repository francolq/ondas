#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    char riff[4];
    int file_size;
    char wave[4];
    char fmt[4];
    int fmt_size;
    short audio_format;
    short num_channels;
    int sample_rate;
    int byte_rate;
    short block_align;
    short bits_per_sample;
    char data[4];
    int data_size;
} WavHeader;

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <wav_file>\n", argv[0]);
        return 1;
    }

    FILE *fp = fopen(argv[1], "rb");
    if (!fp) {
        perror("Failed to open file");
        return 1;
    }

    WavHeader header;
    fread(&header, sizeof(WavHeader), 1, fp);

    printf("RIFF: %.4s\n", header.riff);
    printf("WAVE: %.4s\n", header.wave);
    printf("File size: %d bytes\n", header.file_size + 8);
    printf("Audio format: %d\n", header.audio_format);
    printf("Channels: %d\n", header.num_channels);
    printf("Sample rate: %d Hz\n", header.sample_rate);
    printf("Byte rate: %d bytes/sec\n", header.byte_rate);
    printf("Bits per sample: %d\n", header.bits_per_sample);
    printf("Data size: %d bytes\n", header.data_size);
    printf("Duration: %.2f seconds\n", (double)header.data_size / header.byte_rate);

    fclose(fp);
    return 0;
}
