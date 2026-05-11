from textual.app import App, ComposeResult
from textual.containers import Grid, Horizontal
from textual.widgets import Button, Label, Log
from textual import on
import sounddevice as sd
import soundfile as sf
import numpy as np
import mido
import sys
import argparse
import os
import threading

SAMPLE_RATE = 44100
BPM = 160
SAMPLES_PER_STEP = int(SAMPLE_RATE * 60 / BPM / 4)
# LEVEL_CHARS = {0: " ", 25: "░", 50: "▒", 75: "▓", 100: "█"}
LEVEL_CHARS = {0: "0", 25: "2", 50: "5", 75: "7", 100: "1"}
LEVELS = [0, 25, 50, 75, 100]

PAD_TO_NOTE = dict((i, 36 + i) for i in range(16))
NOTE_TO_PAD = {v: k for k, v in PAD_TO_NOTE.items()}


class Voice:
    __slots__ = ("sample", "pos", "volume")

    def __init__(self, sample, volume):
        self.sample = sample
        self.pos = 0
        self.volume = volume


class DrumMachine(App):
    CSS = """
    DrumMachine {
        align: center middle;
    }
    #controls {
        width: 80%;
        height: 3;
    }
    #controls Label {
        width: auto;
        margin: 0 2;
    }
    #play-btn {
        width: 10;
        margin: 0 2;
    }
    #steps-row {
        width: 80%;
        height: 5;
    }
    #steps-row Button {
        width: 5;
        min-width: 5;
        height: 3;
        min-height: 3;
        padding: 0;
        margin: 0 0;
        border: none tall;
    }
    Button.step-off {
        background: #444;
        color: #666;
    }
    Button.step-on {
        background: #2a7a2a;
        color: #aaffaa;
    }
    Button.current-step {
        background: #c8a000 !important;
        color: #000 !important;
        text-style: bold;
    }
    Button.step-cursor {
        text-style: reverse !important;
    }
    Grid {
        width: 80%;
        height: 50%;
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
        height: 20%;
        border: solid green;
    }
    """

    def __init__(self, midi_port, sample_files, pattern=None):
        super().__init__()
        self.midi_port = midi_port
        self.sample_files = sample_files
        self.active_pads = set()
        self.samples = []
        self.sample_srs = []
        self.steps = [[0] * 16 for _ in range(16)]
        self._auto_start = pattern is not None
        if pattern:
            for step, pad in enumerate(pattern):
                if 1 <= pad <= 16:
                    self.steps[pad - 1][step] = 100
        self.selected_pad = 0
        self.cursor_step = 0
        self.stream = None
        self.current_voice = None
        self.master_volume = 1.0
        self.audio_lock = threading.Lock()

        # Sequencer state — owned by audio callback thread
        self.step_samples_accumulated = 0
        self.current_step = -1
        self.playing = False

    def compose(self) -> ComposeResult:
        with Horizontal(id="controls"):
            yield Label("Pad 1:", id="selected-pad-label")
            yield Button("▶ Play", id="play-btn")
        with Horizontal(id="steps-row"):
            for i in range(16):
                yield Button(" ", id=f"step_{i}", classes="step-off")
        labels = []
        for i in range(16):
            if i < len(self.sample_files):
                name = os.path.splitext(os.path.basename(self.sample_files[i]))[0]
                labels.append(f"{i+1}\n{name}" if len(name) <= 8 else f"{i+1}\n{name[:8]}…")
            else:
                labels.append(f"{i+1}")
        yield Grid(*[Button(l, id=f"pad_{i}") for i, l in enumerate(labels)])
        yield Log("Drum machine ready.", id="log")

    def on_mount(self):
        self.log_widget = self.query_one("#log", Log)
        self.load_samples()
        self.select_pad(0)
        self.stream = sd.OutputStream(
            channels=1,
            samplerate=SAMPLE_RATE,
            callback=self.audio_callback,
        )
        self.stream.start()
        if self._auto_start:
            self.toggle_play()

    def load_samples(self):
        for i, path in enumerate(self.sample_files):
            try:
                sample, sr = sf.read(path, dtype="float32")
                if len(sample.shape) > 1:
                    sample = sample.mean(axis=1)
                if sr != SAMPLE_RATE:
                    old = np.arange(len(sample))
                    new = np.linspace(0, len(sample) - 1, int(len(sample) * SAMPLE_RATE / sr))
                    sample = np.interp(new, old, sample).astype(np.float32)
                self.samples.append(sample)
                self.sample_srs.append(SAMPLE_RATE)
                name = os.path.basename(path)
                self.log_widget.write(f"Loaded pad {i+1}: {name} ({len(sample)} samples, resampled to {SAMPLE_RATE} Hz)\n")
            except Exception as e:
                self.log_widget.write(f"Pad {i+1}: failed to load {path}: {e}\n")
                self.samples.append(None)
                self.sample_srs.append(None)

    def select_pad(self, pad_num):
        self.selected_pad = pad_num
        if pad_num < len(self.sample_files):
            name = os.path.splitext(os.path.basename(self.sample_files[pad_num]))[0]
            self.query_one("#selected-pad-label", Label).update(f"Pad {pad_num+1}: {name}")
        else:
            self.query_one("#selected-pad-label", Label).update(f"Pad {pad_num+1}")
        self.update_step_display()

    def trigger_pad(self, pad_num, velocity=100):
        if 0 <= pad_num < len(self.samples) and self.samples[pad_num] is not None:
            self.log_widget.write(f"Pad {pad_num + 1} triggered (vel={velocity})\n")
            button = self.query_one(f"#pad_{pad_num}", Button)
            button.add_class("active")
            sample_data = self.samples[pad_num] * (velocity / 127)
            with self.audio_lock:
                self.current_voice = Voice(sample_data, 1.0)

    def release_pad(self, pad_num):
        if 0 <= pad_num < 16:
            button = self.query_one(f"#pad_{pad_num}", Button)
            button.remove_class("active")

    def toggle_step(self, step_num):
        current = self.steps[self.selected_pad][step_num]
        self.steps[self.selected_pad][step_num] = LEVELS[(LEVELS.index(current) + 1) % len(LEVELS)]
        self._update_step_button(step_num)

    def toggle_play(self):
        if self.playing:
            prev = self.current_step
            self.playing = False
            self.query_one("#play-btn", Button).label = "▶ Play"
            if prev >= 0:
                self._update_step_button(prev)
        else:
            self.playing = True
            self.current_step = -1
            self.step_samples_accumulated = SAMPLES_PER_STEP
            self.query_one("#play-btn", Button).label = "■ Stop"

    def audio_callback(self, outdata, frames, time, status):
        outdata.fill(0)

        with self.audio_lock:
            v = self.current_voice

        if v is not None:
            avail = min(frames, len(v.sample) - v.pos)
            if avail > 0:
                end = v.pos + avail
                outdata[0:avail, 0] = v.sample[v.pos:end] * v.volume * self.master_volume
                v.pos += avail

        np.clip(outdata, -1.0, 1.0, out=outdata)

        self.step_samples_accumulated += frames
        triggered = False
        prev_step = self.current_step
        while self.playing and self.step_samples_accumulated >= SAMPLES_PER_STEP:
            self.step_samples_accumulated -= SAMPLES_PER_STEP
            self.current_step = (self.current_step + 1) % 16
            triggered = True
            for pad in range(16):
                level = self.steps[pad][self.current_step]
                if level > 0:
                    sample = self.samples[pad]
                    if sample is not None:
                        with self.audio_lock:
                            self.current_voice = Voice(sample.copy(), level / 100)
        if triggered:
            self.call_from_thread(self._update_playhead, prev_step, self.current_step)

    def _update_playhead(self, prev, new):
        if prev >= 0:
            self._update_step_button(prev)
        self._update_step_button(new)

    def _update_step_button(self, i):
        button = self.query_one(f"#step_{i}", Button)
        level = self.steps[self.selected_pad][i]
        is_current = (i == self.current_step) and self.playing
        button.label = LEVEL_CHARS[level]
        button.remove_class("step-off", "step-on", "current-step", "step-cursor")
        if level > 0:
            button.add_class("step-on")
        else:
            button.add_class("step-off")
        if is_current:
            button.add_class("current-step")
        if i == self.cursor_step:
            button.add_class("step-cursor")

    def update_step_display(self):
        for i in range(16):
            self._update_step_button(i)

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if not button_id:
            return
        if button_id.startswith("pad_"):
            pad_num = int(button_id.replace("pad_", ""))
            self.select_pad(pad_num)
            self.trigger_pad(pad_num)
        elif button_id.startswith("step_"):
            step_num = int(button_id.replace("step_", ""))
            self.toggle_step(step_num)
        elif button_id == "play-btn":
            self.toggle_play()

    def on_midi(self, msg):
        if msg.type == "note_on" and msg.velocity > 0:
            pad_num = NOTE_TO_PAD.get(msg.note)
            if pad_num is not None:
                self.trigger_pad(pad_num, msg.velocity)
                self.active_pads.add(pad_num)
        elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
            pad_num = NOTE_TO_PAD.get(msg.note)
            if pad_num in self.active_pads:
                self.release_pad(pad_num)
                self.active_pads.discard(pad_num)
        elif msg.type == "control_change" and msg.control == 3:
            self.master_volume = msg.value / 127.0
        elif msg.type == "control_change" and msg.control == 9:
            old = self.cursor_step
            self.cursor_step = int(msg.value * 15 / 127)
            self._update_step_button(old)
            self._update_step_button(self.cursor_step)
        elif msg.type == "control_change" and msg.control == 12:
            level = int(msg.value / 26) * 25
            if level > 100:
                level = 100
            self.steps[self.selected_pad][self.cursor_step] = level
            self._update_step_button(self.cursor_step)

    def on_unmount(self):
        if self.stream:
            self.stream.stop()
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
    port_name = inputs[int(choice)]
    print(f"\nListening on: {port_name}")
    midi_port = mido.open_input(port_name)
    return midi_port


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Drum Machine with 16-step sequencer")
    parser.add_argument("samples", nargs="+", help="WAV files for pads 1-16")
    parser.add_argument("--pattern", nargs=16, type=int,
                        help="16-step pattern: pad numbers 0-16 (0=silence)")
    args = parser.parse_args()

    samples = args.samples[:16]
    midi_port = connect_midi()
    app = DrumMachine(midi_port, samples, pattern=args.pattern)
    if midi_port:
        midi_port.callback = app.on_midi
    app.run()
