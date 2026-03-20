from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Label, Log
from textual_slider import Slider
from textual import on
import sounddevice as sd
import numpy as np

SAMPLE_RATE = 44100


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

    def __init__(self):
        super().__init__()
        self.amplitude = 0.5
        self.frequency = 440
        self.start_idx = 0
        self.stream = None
        self.amplitude_label: Label | None = None
        self.frequency_label: Label | None = None
        self.log_widget: Log | None = None

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
            self.log_widget.write(f"Audio status: {status}\n")
        t = (self.start_idx + np.arange(frames)) / SAMPLE_RATE
        t = t.reshape(-1, 1)
        outdata[:] = self.amplitude * np.sin(2 * np.pi * self.frequency * t)
        self.start_idx += frames

    @on(Slider.Changed)
    def on_slider_changed(self, event):
        if event.slider.id == "amplitude":
            self.amplitude = event.slider.value / 100
            self.amplitude_label.update(f"Amplitude: {self.amplitude:.2f}\n")
            self.log_widget.write(f"Amplitude changed to {self.amplitude:.2f}\n")
        elif event.slider.id == "frequency":
            self.frequency = 20 + event.slider.value * 19.8  # 20-2000 Hz
            self.frequency_label.update(f"Frequency: {int(self.frequency)} Hz\n")
            self.log_widget.write(f"Frequency changed to {int(self.frequency)} Hz\n")

    def on_unmount(self):
        if self.stream:
            self.stream.close()


if __name__ == "__main__":
    app = WaveApp()
    app.run()
