#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

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
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <input.wav> <output.png> [width] [height]\n", argv[0]);
        return 1;
    }

    int width = argc > 3 ? atoi(argv[3]) : 800;
    int height = argc > 4 ? atoi(argv[4]) : 200;

    FILE *fp = fopen(argv[1], "rb");
    if (!fp) {
        perror("Failed to open file");
        return 1;
    }

    WavHeader header;
    fread(&header, sizeof(WavHeader), 1, fp);

    if (strncmp(header.riff, "RIFF", 4) != 0 || strncmp(header.wave, "WAVE", 4) != 0) {
        fprintf(stderr, "Not a valid WAV file\n");
        fclose(fp);
        return 1;
    }

    int num_samples = header.data_size / (header.bits_per_sample / 8);
    short *samples = malloc(num_samples * sizeof(short));
    fread(samples, sizeof(short), num_samples, fp);
    fclose(fp);

    unsigned char *img = malloc(width * height * 3);
    memset(img, 255, width * height * 3);

    int samples_per_pixel = num_samples / width;
    if (samples_per_pixel < 1) samples_per_pixel = 1;

    for (int x = 0; x < width; x++) {
        int start = x * samples_per_pixel;
        int end = start + samples_per_pixel;
        if (end > num_samples) end = num_samples;

        short min_val = 0;
        short max_val = 0;
        for (int i = start; i < end; i++) {
            if (samples[i] < min_val) min_val = samples[i];
            if (samples[i] > max_val) max_val = samples[i];
        }

        int y_min = height / 2 + (int)((double)min_val / 32768.0 * (height / 2));
        int y_max = height / 2 + (int)((double)max_val / 32768.0 * (height / 2));

        for (int y = y_min; y <= y_max && y < height; y++) {
            if (y >= 0) {
                img[(y * width + x) * 3 + 0] = 0;
                img[(y * width + x) * 3 + 1] = 0;
                img[(y * width + x) * 3 + 2] = 0;
            }
        }
    }

    stbi_write_png(argv[2], width, height, 3, img, width * 3);

    free(samples);
    free(img);

    printf("Created %s (%dx%d)\n", argv[2], width, height);
    return 0;
}
