import sys
import mido
import numpy as np
import soundfile as sf


def note_on_times(mid):
    # absolute seconds of every note_on (velocity > 0), merged across tracks
    # and respecting any set_tempo changes
    tempo = 500000  # default 120 BPM, microseconds per quarter note
    abs_sec = 0.0
    times = []
    for msg in mido.merge_tracks(mid.tracks):
        abs_sec += mido.tick2second(msg.time, mid.ticks_per_beat, tempo)
        if msg.type == "set_tempo":
            tempo = msg.tempo
        elif msg.type == "note_on" and msg.velocity > 0:
            times.append(abs_sec)
    return sorted(times)


def main():
    flags = {"--to-end", "--stretch-midi"}
    to_end = "--to-end" in sys.argv[1:]
    stretch_midi = "--stretch-midi" in sys.argv[1:]
    args = [a for a in sys.argv[1:] if a not in flags]
    if len(args) < 2:
        print("Usage: python split_wav_by_midi.py <input.wav> <input.mid> "
              "[output_prefix] [--to-end] [--stretch-midi]")
        sys.exit(1)

    wav_path = args[0]
    mid_path = args[1]
    prefix = args[2] if len(args) > 2 else wav_path.rsplit(".", 1)[0]

    audio, sr = sf.read(wav_path)
    info = sf.info(wav_path)
    orig_dtype = audio.dtype

    mid = mido.MidiFile(mid_path)
    times = note_on_times(mid)

    # line the note_on times up with the WAV. By default stretch the WAV to the
    # MIDI length (varispeed, changes pitch); with --stretch-midi instead leave
    # the WAV untouched and scale the MIDI times onto the WAV length (no repitch)
    target = int(round(mid.length * sr))
    if stretch_midi:
        factor = len(audio) / target if target else 1.0
        times = [t * factor for t in times]
        print(f"Scaled MIDI times by {factor:.4f} "
              f"({mid.length:.3f}s -> {len(audio) / sr:.3f}s); "
              f"WAV unchanged (no repitch)")
    elif len(audio) != target:
        old = np.arange(len(audio))
        new = np.linspace(0, len(audio) - 1, target)
        if audio.ndim > 1:
            audio = np.stack([np.interp(new, old, audio[:, c])
                              for c in range(audio.shape[1])], axis=1)
        else:
            audio = np.interp(new, old, audio)
        audio = np.asarray(audio, dtype=orig_dtype)
        print(f"Stretched {len(old)} -> {target} frames "
              f"({len(old) / sr:.3f}s -> {target / sr:.3f}s)")
    else:
        print(f"WAV length matches MIDI length ({target} frames); no stretch")

    total = len(audio)

    if to_end:
        # each segment starts at a note_on and runs to the end of the audio
        segments = [(int(round(t * sr)), total)
                    for t in times if 0 <= t * sr < total]
    else:
        # split points are the note_on times; add a leading 0 if the first hit
        # is not at the very start, and the MIDI length as the final boundary
        bounds = [int(round(t * sr)) for t in times if 0 <= t * sr <= total]
        if bounds and bounds[0] > 0:
            bounds.insert(0, 0)
        bounds.append(total)
        segments = zip(bounds, bounds[1:])

    count = 0
    for start, end in segments:
        if end <= start:
            continue
        out = f"{prefix}_{count:02d}.wav"
        sf.write(out, audio[start:end], sr, subtype=info.subtype)
        print(f"{out}: {start / sr:.3f}s - {end / sr:.3f}s ({end - start} frames)")
        count += 1

    print(f"Wrote {count} segment(s) from {wav_path} using {len(times)} note_on(s)")


if __name__ == "__main__":
    main()
