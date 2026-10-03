import sys
import mido


def main():
    if len(sys.argv) < 2:
        print("Usage: python midi_dump.py <input.mid>")
        sys.exit(1)

    path = sys.argv[1]
    mid = mido.MidiFile(path)

    print(f"File: {path}")
    print(f"Type: {mid.type}  Tracks: {len(mid.tracks)}  "
          f"Ticks per beat: {mid.ticks_per_beat}")
    print("Leading number = absolute tick position")

    for i, track in enumerate(mid.tracks):
        print(f"\nTrack {i}: {track.name}")
        abs_ticks = 0
        for msg in track:
            abs_ticks += msg.time
            print(f"  {abs_ticks:>8}  {msg}")


if __name__ == "__main__":
    main()
