from textual.app import App, ComposeResult
from textual.containers import Grid
from textual.widgets import Button, Log
from textual import on
import mido
import sounddevice as sd
import soundfile as sf
import sys
import argparse

BASE_NOTE = 36


class SamplerApp(App):
    CSS = """
    SamplerApp {
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

    def __init__(self, midi_port, sample_file):
        super().__init__()
        self.midi_port = midi_port
        self.sample_file = sample_file
        self.active_pads = set()
        self.sample = None
        self.sample_sr = None
        self.stream = None

    def compose(self) -> ComposeResult:
        yield Grid(*[Button(f"{i+1}", id=f"pad_{i}") for i in range(16)])
        yield Log("Sampler ready. Click a pad or use MIDI (notes 36-51).", id="log")

    def on_mount(self):
        self.log_widget = self.query_one("#log", Log)
        self.load_sample()
        self.start_stream()

    def load_sample(self):
        try:
            self.sample, self.sample_sr = sf.read(self.sample_file, dtype='float32')
            self.log_widget.write(f"Loaded: {self.sample_file} ({len(self.sample)} samples, {self.sample_sr} Hz)\n")
        except FileNotFoundError:
            self.log_widget.write(f"Sample not found: {self.sample_file}\n")
        except Exception as e:
            self.log_widget.write(f"Error loading {self.sample_file}: {e}\n")

    def start_stream(self):
        if self.sample is None:
            return
        self.stream = sd.OutputStream(
            channels=self.sample.shape[1] if len(self.sample.shape) > 1 else 1,
            samplerate=self.sample_sr,
            callback=self.audio_callback,
        )
        self.stream.start()

    def audio_callback(self, outdata, frames, time, status):
        if status:
            self.log_widget.write(f"Audio status: {status}\n")

    def trigger_pad(self, pad_num, velocity=100):
        if 0 <= pad_num < 16:
            self.log_widget.write(f"Pad {pad_num + 1} triggered (vel={velocity})\n")
            button = self.query_one(f"#pad_{pad_num}", Button)
            button.add_class("active")

            if self.sample is not None and self.stream is not None:
                sd.stop()
                num_samples = len(self.sample)
                start_frame = int((pad_num / 16) * num_samples)
                sd.play(self.sample[start_frame:], self.sample_sr)

    def release_pad(self, pad_num):
        if 0 <= pad_num < 16:
            self.log_widget.write(f"Pad {pad_num + 1} released\n")
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
            pad_num = msg.note - BASE_NOTE
            if 0 <= pad_num < 16:
                self.trigger_pad(pad_num, msg.velocity)
                self.active_pads.add(pad_num)
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            pad_num = msg.note - BASE_NOTE
            if pad_num in self.active_pads:
                self.release_pad(pad_num)
                self.active_pads.discard(pad_num)

    def on_unmount(self):
        if self.stream:
            self.stream.close()
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
    else:
        port_name = inputs[int(choice)]

    print(f"\nListening on: {port_name}")
    midi_port = mido.open_input(port_name)
    return midi_port


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WAV Sampler with MIDI support")
    parser.add_argument("sample", help="Path to the WAV sample file")
    args = parser.parse_args()

    midi_port = connect_midi()
    app = SamplerApp(midi_port, args.sample)

    if midi_port:
        midi_port.callback = app.on_midi

    app.run()
