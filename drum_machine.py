from textual.app import App, ComposeResult
from textual.containers import Grid
from textual.widgets import Button, Log
from textual import on
import mido
import sounddevice as sd
import soundfile as sf
import sys
import argparse
import os

# M-AUDIO Oxygen25 keyboard:
# PAD_TO_NOTE = {
#     0: 36, 1: 37, 2: 38, 3: 39,
#     4: 41, 5: 42, 6: 43, 7: 44,
#     8: 48, 9: 49, 10: 50, 11: 51,
#     12: 53, 13: 54, 14: 55, 15: 56,
# }
# AKAI MPC218 pads:
PAD_TO_NOTE = dict((i, 36 + i) for i in range(16))
NOTE_TO_PAD = {v: k for k, v in PAD_TO_NOTE.items()}


class DrumMachine(App):
    CSS = """
    DrumMachine {
        align: center middle;
    }
    Grid {
        width: 80%;
        height: 60%;
        grid-size: 4 4;
        grid-gutter: 1 1;
    }
    Button {
        width: 100%;
        height: 100%;
    }
    Button.active {
        background: darkblue;
        color: white;
    }
    Log {
        width: 80%;
        height: 30%;
        border: solid green;
    }
    """

    def __init__(self, midi_port, sample_files):
        super().__init__()
        self.midi_port = midi_port
        self.sample_files = sample_files
        self.active_pads = set()
        self.samples = []
        self.sample_srs = []

    def compose(self) -> ComposeResult:
        labels = []
        for i in range(16):
            if i < len(self.sample_files):
                name = os.path.splitext(os.path.basename(self.sample_files[i]))[0]
                labels.append(f"{i+1}\n{name}" if len(name) <= 8 else f"{i+1}\n{name[:8]}…")
            else:
                labels.append(f"{i+1}")
        yield Grid(*[Button(l, id=f"pad_{i}") for i, l in enumerate(labels)])
        yield Log("Drum machine ready. Click a pad or use MIDI (36-39, 41-44, 48-51, 53-56).", id="log")

    def on_mount(self):
        self.log_widget = self.query_one("#log", Log)
        self.load_samples()

    def load_samples(self):
        for i, path in enumerate(self.sample_files):
            try:
                sample, sr = sf.read(path, dtype='float32')
                self.samples.append(sample)
                self.sample_srs.append(sr)
                name = os.path.basename(path)
                self.log_widget.write(f"Loaded pad {i+1}: {name} ({len(sample)} samples, {sr} Hz)\n")
            except Exception as e:
                self.log_widget.write(f"Pad {i+1}: failed to load {path}: {e}\n")
                self.samples.append(None)
                self.sample_srs.append(None)

    def trigger_pad(self, pad_num, velocity=100):
        if 0 <= pad_num < len(self.samples) and self.samples[pad_num] is not None:
            self.log_widget.write(f"Pad {pad_num + 1} triggered (vel={velocity})\n")
            button = self.query_one(f"#pad_{pad_num}", Button)
            button.add_class("active")
            sample = self.samples[pad_num] * (velocity / 127)
            sd.play(sample, self.sample_srs[pad_num])

    def release_pad(self, pad_num):
        if 0 <= pad_num < 16:
            button = self.query_one(f"#pad_{pad_num}", Button)
            button.remove_class("active")

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id:
            pad_num = int(button_id.replace("pad_", ""))
            self.trigger_pad(pad_num)

    def on_midi(self, msg):
        if msg.type == 'note_on' and msg.velocity > 0:
            pad_num = NOTE_TO_PAD.get(msg.note)
            if pad_num is not None:
                self.trigger_pad(pad_num, msg.velocity)
                self.active_pads.add(pad_num)
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            pad_num = NOTE_TO_PAD.get(msg.note)
            if pad_num in self.active_pads:
                self.release_pad(pad_num)
                self.active_pads.discard(pad_num)

    def on_unmount(self):
        if self.midi_port:
            self.midi_port.close()


def connect_midi():
    print("Available MIDI input devices:")
    inputs = mido.get_input_names()
    if not inputs:
        print("  No devices found.")
        return
    for i, name in enumerate(inputs):
        print(f"  [{i}] {name}")
    choice = input("\nSelect device index (or press Enter for none): ").strip()
    if choice == "":
        return
    port_name = inputs[int(choice)]
    print(f"\nListening on: {port_name}")
    midi_port = mido.open_input(port_name)
    return midi_port


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Drum Machine with MIDI support")
    parser.add_argument("samples", nargs="+", help="WAV files for pads 1-16")
    args = parser.parse_args()

    samples = args.samples[:16]
    midi_port = connect_midi()
    app = DrumMachine(midi_port, samples)
    if midi_port:
        midi_port.callback = app.on_midi
    app.run()
