# Low-pass filter with real-time cutoff adjustment
#
# Applied to white noise for 5 seconds, with cutoff going from 20.000 to 20 Hz.
# Based on an all-pass filter.
#
# As explained by WolfSound in
# "Simple Lowpass and Highpass Filters with Python Implementation [AudioFX #009]"
# https://www.youtube.com/watch?v=Aht4letBAmA

import numpy as np
import sounddevice as sd

sampling_rate = 44100
duration_in_seconds = 5
highpass = False  # it could also be a high-pass filter!
amplitude = 0.3

duration_in_samples = int(duration_in_seconds * sampling_rate)
white_noise = np.random.uniform(-1, 1, duration_in_samples)
input_signal = white_noise

cutoff_frequency = np.geomspace(20000, 20, input_signal.shape[0])

allpass_output = np.zeros_like(input_signal)

# "inner buffer for the all-pass filter"
dn_1 = 0

for n in range(input_signal.shape[0]):
    break_frequency = cutoff_frequency[n]

    tan = np.tan(np.pi * break_frequency / sampling_rate)
    a1 = (tan - 1) / (tan + 1)

    # allpass_output[n] = a1 * input_signal[n] + dn_1
    # also try without dn_1:
    allpass_output[n] = a1 * input_signal[n]

    dn_1 = input_signal[n] - a1 * allpass_output[n]

if highpass:
    allpass_output *= -1

filter_output = input_signal + allpass_output

filter_output *= 0.5

filter_output *= amplitude

sd.play(filter_output, sampling_rate)
sd.wait()
