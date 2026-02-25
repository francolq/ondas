#include <stdio.h>
#include <math.h>
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

int main() {
    double frequency = 440.0;
    double duration = 1.0;
    int sample_rate = 44100;
    int bits_per_sample = 16;
    int num_channels = 1;
    
    int num_samples = (int)(sample_rate * duration);
    int data_size = num_samples * num_channels * (bits_per_sample / 8);
    int file_size = 36 + data_size;
    
    WavHeader header;
    memcpy(header.riff, "RIFF", 4);
    header.file_size = file_size;
    memcpy(header.wave, "WAVE", 4);
    memcpy(header.fmt, "fmt ", 4);
    header.fmt_size = 16;
    header.audio_format = 1;
    header.num_channels = num_channels;
    header.sample_rate = sample_rate;
    header.byte_rate = sample_rate * num_channels * (bits_per_sample / 8);
    header.block_align = num_channels * (bits_per_sample / 8);
    header.bits_per_sample = bits_per_sample;
    memcpy(header.data, "data", 4);
    header.data_size = data_size;
    
    FILE *fp = fopen("sine.wav", "wb");
    if (!fp) {
        perror("Failed to open file");
        return 1;
    }
    
    fwrite(&header, sizeof(WavHeader), 1, fp);
    
    double amplitude = 16000;
    for (int i = 0; i < num_samples; i++) {
        double sample = amplitude * sin(2.0 * M_PI * frequency * i / sample_rate);
        short s = (short)sample;
        printf("%i\n", s);
        fwrite(&s, sizeof(short), 1, fp);
    }
    
    fclose(fp);
    printf("Created sine.wav: %d Hz, %.1f seconds\n", (int)frequency, duration);
    return 0;
}
