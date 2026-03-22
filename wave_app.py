from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Label, Log
from textual_slider import Slider
from textual import on
import sounddevice as sd
import numpy as np
import mido

SAMPLE_RATE = 44100

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def note_name(note):
    octave = (note // 12) - 1
    name = NOTE_NAMES[note % 12]
    return f"{name}{octave}"


def midi_to_frequency(note):
    return 440.0 * (2 ** ((note - 69) / 12))


class WaveApp(App):
    CSS = """
    WaveApp {
        align: center middle;
    }
    Horizontal {
        height: 70%;
        width: 100%;
    }
    Vertical {
        width: 1fr;
        height: 100%;
    }
    Slider {
        width: 100%;
    }
    Label {
        width: 100%;
        height: 3;
        content-align: center bottom;
    }
    Log {
        width: 100%;
        height: 30%;
        border: solid green;
    }
    """

    def __init__(self, midi_port):
        super().__init__()
        self.amplitude = 0.5
        self.frequency = 440
        self.start_idx = 0
        self.stream = None
        self.amplitude_label: Label | None = None
        self.frequency_label: Label | None = None
        self.log_widget: Log | None = None
        self.midi_port = midi_port
        self._skip_slider_event = False

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical():
                self.amplitude_label = Label("Amplitude: 0.50")
                yield self.amplitude_label
                yield Slider(0, 100, value=50, id="amplitude")
            with Vertical():
                self.frequency_label = Label("Frequency: 440 Hz")
                yield self.frequency_label
                yield Slider(0, 100, value=50, id="frequency")
        self.log_widget = Log("Log:", id="log")
        yield self.log_widget

    def on_mount(self):
        self.log_widget.write("Audio stream started\n")
        self.stream = sd.OutputStream(
            channels=1,
            samplerate=SAMPLE_RATE,
            callback=self.audio_callback
        )
        self.stream.start()

    def audio_callback(self, outdata, frames, time, status):
        if status:
            if status.output_underflow:
                self.log_widget.write(f"Output underflow: blocksize={frames}\n")
            else:
                self.log_widget.write(f"Audio status: {status}\n")

        t = (self.start_idx + np.arange(frames)) / SAMPLE_RATE
        t = t.reshape(-1, 1)
        outdata[:] = self.amplitude * np.sin(2 * np.pi * self.frequency * t)
        self.start_idx += frames

    @on(Slider.Changed)
    def on_slider_changed(self, event):
        if self._skip_slider_event:
            self._skip_slider_event = False
            self.log_widget.write(f"Skip event\n")
            return
        if event.slider.id == "amplitude":
            self.amplitude = event.slider.value / 100
            self.amplitude_label.update(f"Amplitude: {self.amplitude:.2f}\n")
            self.log_widget.write(f"Amplitude changed to {self.amplitude:.2f}\n")
        elif event.slider.id == "frequency":
            self.frequency = 20 + event.slider.value * 19.8  # 20-2000 Hz
            self.frequency_label.update(f"Frequency: {int(self.frequency)} Hz\n")
            self.log_widget.write(f"Frequency changed to {int(self.frequency)} Hz\n")

    def on_midi(self, msg):
        if msg.type == 'note_on' and msg.velocity > 0:
            freq = midi_to_frequency(msg.note)
            name = note_name(msg.note)
            if freq == self.frequency:
                self.log_widget.write(f"Repeated note On: {name}\n")
                return
            self.frequency = freq
            slider_val = int((self.frequency - 20) / 19.8)
            slider_val = max(0, min(100, slider_val))
            self._skip_slider_event = True
            # won't trigger skip_slider_event event if value is not changed
            # FIXME: sometimes freq will change but slider position will not
            self.query_one("#frequency", Slider).value = slider_val
            self.frequency_label.update(f"Frequency: {int(self.frequency)} Hz (MIDI: {name})\n")
            self.log_widget.write(f"Note On: {name}\n")
        elif msg.type == 'control_change' and msg.control == 110:
            # setting the slider triggers the on_slider_changed event
            # self.amplitude = msg.value / 127.0
            self.query_one("#amplitude", Slider).value = int(msg.value * 100 / 127)
            self.log_widget.write(f"CC 110: {msg.value}\n")

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
    midi_port = connect_midi()
    app = WaveApp(midi_port)

    if midi_port:
        midi_port.callback = app.on_midi

    app.run()
