from textual.app import App, ComposeResult
from textual.containers import Grid, Horizontal, Vertical
from textual.widgets import Button, Label, Log
from textual import on
import sounddevice as sd
import soundfile as sf
import numpy as np
import mido
import sys
import argparse
import os
import random
import threading

SAMPLE_RATE = 44100
BPM = 160
SAMPLES_PER_STEP = int(SAMPLE_RATE * 60 / BPM / 4)
LEVEL_CHARS = {0: "0", 25: "2", 50: "5", 75: "7", 100: "1"}
LEVELS = [0, 25, 50, 75, 100]

# Pads 14 and 16 are not sounds: 14 = quantize toggle, 16 = play/stop
# (stored 0-indexed, so pad 16 is index 15).
QUANTIZE_PAD = 14
PLAY_PAD = 15
# Pad 13 (index 12) toggles cursor selection of all steps at once.
SELECT_ALL_PAD = 12

PAD_TO_NOTE = dict((i, 36 + i) for i in range(16))
NOTE_TO_PAD = {v: k for k, v in PAD_TO_NOTE.items()}


class Voice:
    __slots__ = ("sample", "pos", "volume")

    def __init__(self, sample, volume):
        self.sample = sample
        self.pos = 0
        self.volume = volume


class DrumMachine(App):
    # Class attribute that Textual's framework reads automatically:
    # When the user presses v, Textual looks up the action name toggle_view and
    # calls the method named action_ + that name, i.e. action_toggle_view
    BINDINGS = [
        ("v", "toggle_view", "Toggle View"),
        ("s", "save_pattern", "Save Pattern"),
        ("e", "export_midi", "Export MIDI"),
    ]

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
    #playhead-row {
        width: 80%;
        height: 1;
    }
    #playhead-row Label {
        width: 5;
        min-width: 5;
        height: 1;
        content-align: center top;
        color: yellow;
    }
    #voice-row {
        width: 80%;
        height: 1;
    }
    #voice-row Label {
        width: 5;
        min-width: 5;
        height: 1;
        content-align: center top;
        color: cyan;
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
    #history {
        width: 80%;
    }
    #history-title {
        width: auto;
        height: 1;
        color: #aaa;
        text-style: bold;
    }
    #history Horizontal {
        width: 100%;
        height: 1;
    }
    #history Label {
        width: 5;
        min-width: 5;
        height: 1;
        content-align: center top;
        color: #888;
    }
    #saved-patterns {
        width: 80%;
    }
    #saved-patterns-title {
        width: auto;
        height: 1;
        color: #aac;
        text-style: bold;
    }
    #saved-patterns Horizontal {
        width: 100%;
        height: 1;
    }
    #saved-patterns Label {
        width: 5;
        min-width: 5;
        height: 1;
        content-align: center top;
        color: #88a;
    }
    Button.step-off {
        background: #444;
        color: #666;
    }
    Button.step-on {
        background: #2a7a2a;
        color: #aaffaa;
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
        self.fatal_error = None
        # pad display names, computed once from the file names
        self.pad_names = [os.path.splitext(os.path.basename(p))[0] for p in sample_files]
        self.active_pads = set()
        self.samples = []
        self.steps = [(-1, 0) for _ in range(16)]
        self._auto_start = pattern is not None
        if pattern:
            for step, pad in enumerate(pattern):
                if 1 <= pad <= 16:
                    self.steps[step] = (pad - 1, 100)
        self.selected_pad = 0
        self.cursor_step = 0
        self.select_all = False
        self.stream = None
        self.current_voice = None
        self.master_volume = 1.0
        self.rand = 0.0
        self.audio_lock = threading.Lock()
        self.quantize = True
        self.pending_trigger = None
        self.pending_trigger_on = False
        self.steps_view = False
        self.bar_steps = [None] * 16

        # history is a list of rows, where each row is a
        # 16-element list, one entry per step of a completed bar
        # each entry is a 0-based pad index or None
        self.history = []
        initial_pattern = [pad if pad >= 0 else None for pad, level in self.steps]
        self.saved_patterns = [list(initial_pattern) for _ in range(4)]

        # Sequencer state — owned by audio callback thread
        self.step_samples_accumulated = 0
        self.current_step = -1
        self.playing = False

    def compose(self) -> ComposeResult:
        with Horizontal(id="controls"):
            yield Label("Vol: 100%", id="volume-label")
            yield Label("Ran:  0%", id="rand-label")
            yield Label("Pad 1:", id="selected-pad-label")
            yield Label("View: PADS", id="view-label")
        with Horizontal(id="playhead-row"):
            for i in range(16):
                yield Label(" ", id=f"ph_{i}")
        with Horizontal(id="voice-row"):
            for i in range(16):
                yield Label(" ", id=f"voice_{i}")
        with Horizontal(id="steps-row"):
            for i in range(16):
                yield Button(" ", id=f"step_{i}", classes="step-off")
        with Vertical(id="history"):
            yield Label("History", id="history-title")
            for row in range(4):
                with Horizontal(id=f"hist-row-{row}"):
                    for i in range(16):
                        yield Label(" ", id=f"hist_{row}_{i}")
        with Vertical(id="saved-patterns"):
            yield Label("Saved Patterns", id="saved-patterns-title")
            for row in range(4):
                with Horizontal(id=f"spat-row-{row}"):
                    for i in range(16):
                        yield Label(" ", id=f"spat_{row}_{i}")
        buttons = []
        for row in range(4):
            for col in range(4):
                pad_idx = (3 - row) * 4 + col
                if pad_idx == QUANTIZE_PAD:
                    label = f"{QUANTIZE_PAD+1}\nQ: ON"
                elif pad_idx == SELECT_ALL_PAD:
                    label = f"{SELECT_ALL_PAD+1}\nAll:OFF"
                elif pad_idx < PLAY_PAD:
                    if pad_idx < len(self.pad_names):
                        name = self.pad_names[pad_idx]
                        label = f"{pad_idx+1}\n{name}" if len(name) <= 8 else f"{pad_idx+1}\n{name[:8]}…"
                    else:
                        label = f"{pad_idx+1}"
                else:
                    label = f"{PLAY_PAD+1}\n▶Play"
                buttons.append(Button(label, id=f"pad_{pad_idx}"))
        yield Grid(*buttons, id="pads-grid")
        yield Log("Drum machine ready.", id="log")

    # Textual action bound to the v key via class attribute BINDINGS
    def action_toggle_view(self):
        self.steps_view = not self.steps_view
        self._apply_view()
        self.log_widget.write(f"View: {'STEPS' if self.steps_view else 'PADS'}\n")

    def action_save_pattern(self):
        if not self.history:
            self.log_widget.write("Nothing saved: no completed bar in history\n")
            return
        self.saved_patterns.insert(0, list(self.history[0]))
        del self.saved_patterns[4:]
        self._refresh_saved_patterns()
        self.log_widget.write(f"Saved bar to saved_patterns ({len(self.saved_patterns)} saved)\n")

    def action_export_midi(self):
        # Export all saved patterns as consecutive bars into one MIDI file.
        # Each saved pattern is a 16-element list of 0-based pad indices or None.
        # Pad p -> note PAD_TO_NOTE[p] (36 + p); fixed velocity since saved
        # patterns carry no per-step level.
        VELOCITY = 100
        # ticks per beat; one step = a 16th note, one bar = 16 steps = 4 beats
        tpq = 480
        step_ticks = tpq // 4
        note_ticks = step_ticks  # each hit lasts one step

        mid = mido.MidiFile(ticks_per_beat=tpq)
        track = mido.MidiTrack()
        mid.tracks.append(track)
        track.append(mido.MetaMessage("set_tempo",
                                      tempo=mido.bpm2tempo(BPM), time=0))

        delta = 0  # ticks since last emitted event
        for pattern in self.saved_patterns:
            for step in range(16):
                pad = pattern[step] if step < len(pattern) else None
                if pad is not None:
                    note = PAD_TO_NOTE[pad]
                    track.append(mido.Message("note_on", note=note,
                                              velocity=VELOCITY, time=delta))
                    track.append(mido.Message("note_off", note=note,
                                              velocity=0, time=note_ticks))
                    delta = step_ticks - note_ticks
                else:
                    delta += step_ticks

        base = "pattern"
        n = 0
        path = f"{base}.mid"
        while os.path.exists(path):
            n += 1
            path = f"{base}_{n}.mid"
        mid.save(path)
        self.log_widget.write(
            f"Exported {len(self.saved_patterns)} saved pattern(s) to {path}\n")

    def _apply_view(self):
        view_label = self.query_one("#view-label", Label)
        pads = self.query_one("#pads-grid", Grid)
        history = self.query_one("#history", Vertical)
        saved_patterns = self.query_one("#saved-patterns", Vertical)
        if self.steps_view:
            pads.display = False
            history.display = True
            saved_patterns.display = True
            view_label.update("View: STEPS")
        else:
            pads.display = True
            history.display = False
            saved_patterns.display = False
            view_label.update("View: PADS")

    def _refresh_history(self):
        for row in range(4):
            for i in range(16):
                label = self.query_one(f"#hist_{row}_{i}", Label)
                if row < len(self.history):
                    pad = self.history[row][i]
                    label.update(str(pad + 1) if pad is not None else " ")
                else:
                    label.update(" ")

    def _refresh_saved_patterns(self):
        for row in range(4):
            for i in range(16):
                label = self.query_one(f"#spat_{row}_{i}", Label)
                if row < len(self.saved_patterns):
                    pad = self.saved_patterns[row][i]
                    label.update(str(pad + 1) if pad is not None else " ")
                else:
                    label.update(" ")

    def on_mount(self):
        self.log_widget = self.query_one("#log", Log)
        self.volume_label = self.query_one("#volume-label", Label)
        self.rand_label = self.query_one("#rand-label", Label)
        self.load_samples()
        self.select_pad(0)
        self.update_step_display()
        self._apply_view()
        self._refresh_saved_patterns()
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
                    # resample by linear interpolation
                    # (naive resampler: when downsampling high frequencies can alias)
                    old = np.arange(len(sample))
                    new = np.linspace(0, len(sample) - 1, int(len(sample) * SAMPLE_RATE / sr))
                    sample = np.interp(new, old, sample).astype(np.float32)
                self.samples.append(sample)
                name = os.path.basename(path)
                self.log_widget.write(f"Loaded pad {i+1}: {name} ({len(sample)} samples, resampled to {SAMPLE_RATE} Hz)\n")
            except Exception as e:
                self.fatal_error = f"Pad {i+1}: failed to load {path}: {e}"
                self.log_widget.write(self.fatal_error + "\n")
                self.exit()
                return

    def select_pad(self, pad_num):
        self.selected_pad = pad_num
        if pad_num < len(self.pad_names):
            name = self.pad_names[pad_num]
            self.query_one("#selected-pad-label", Label).update(f"Pad {pad_num+1}: {name}")
        else:
            self.query_one("#selected-pad-label", Label).update(f"Pad {pad_num+1}")

    def trigger_pad(self, pad_num, velocity=100):
        if not (0 <= pad_num < len(self.samples)):
            return
        if self.quantize and self.playing:
            self.log_widget.write(f"Pad {pad_num + 1} quantized (vel={velocity})\n")
            self.pending_trigger = (pad_num, velocity)
            self.pending_trigger_on = True
            return
        self.log_widget.write(f"Pad {pad_num + 1} triggered (vel={velocity})\n")
        button = self.query_one(f"#pad_{pad_num}", Button)
        button.add_class("active")
        sample_data = self.samples[pad_num] * (velocity / 127)
        with self.audio_lock:
            self.current_voice = Voice(sample_data, 1.0)

    def release_pad(self, pad_num):
        if not (0 <= pad_num < 16):
            return
        button = self.query_one(f"#pad_{pad_num}", Button)
        button.remove_class("active")
        self.pending_trigger_on = False

    def toggle_step(self, step_num):
        pad, level = self.steps[step_num]
        if level == 0 or pad != self.selected_pad:
            self.steps[step_num] = (self.selected_pad, 25)
        else:
            next_level = LEVELS[(LEVELS.index(level) + 1) % len(LEVELS)]
            self.steps[step_num] = (self.selected_pad, next_level) if next_level > 0 else (-1, 0)
        self._update_step_button(step_num)
        self._update_voice_cell(step_num)

    def toggle_quantize(self):
        self.quantize = not self.quantize
        self.query_one(f"#pad_{QUANTIZE_PAD}", Button).label = f"{QUANTIZE_PAD+1}\nQ: ON" if self.quantize else f"{QUANTIZE_PAD+1}\nQ:OFF"
        self.log_widget.write(f"Quantization {'ON' if self.quantize else 'OFF'}\n")

    def toggle_select_all(self):
        self.select_all = not self.select_all
        self.query_one(f"#pad_{SELECT_ALL_PAD}", Button).label = (
            f"{SELECT_ALL_PAD+1}\nAll: ON" if self.select_all
            else f"{SELECT_ALL_PAD+1}\nAll:OFF")
        for i in range(16):
            self._update_step_button(i)
        self.log_widget.write(f"Select all steps {'ON' if self.select_all else 'OFF'}\n")

    def toggle_play(self):
        if self.playing:
            prev = self.current_step
            self.playing = False
            if prev >= 0:
                self._set_playhead(prev, False)
            self.query_one(f"#pad_{PLAY_PAD}", Button).label = f"{PLAY_PAD+1}\n▶Play"
        else:
            self.playing = True
            self.current_step = -1
            self.step_samples_accumulated = SAMPLES_PER_STEP
            self.pending_trigger = None
            self.bar_steps = [None] * 16
            self.query_one(f"#pad_{PLAY_PAD}", Button).label = f"{PLAY_PAD+1}\n■Stop"

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
            prev = self.current_step
            self.current_step = (self.current_step + 1) % 16
            if prev == 15 and self.current_step == 0:
                # a bar (steps 0..15) just completed: push it into history
                self.history.insert(0, self.bar_steps)
                del self.history[4:]
                self.bar_steps = [None] * 16
                self.call_from_thread(self._refresh_history)
            triggered = True

            level = 0
            if self.pending_trigger is not None:
                # step is overriden by pressed pad
                pad, level = self.pending_trigger
                if not self.pending_trigger_on:
                    # note was released
                    self.pending_trigger = None
            else:
                pad, level = self.steps[self.current_step]
                if level > 0 and self.rand > 0 and random.random() < self.rand:
                    # random swap: pick a saved pattern uniformly, use its pad
                    # at the current step (skip if the saved step is empty)
                    if self.saved_patterns:
                        pattern = random.choice(self.saved_patterns)
                        candidate = pattern[self.current_step]
                        if candidate is not None:
                            pad = candidate
            if level > 0 and 0 <= pad < len(self.samples):
                sample = self.samples[pad]
                with self.audio_lock:
                    self.current_voice = Voice(sample.copy(), level / 100)
                self.bar_steps[self.current_step] = pad
        if triggered:
            # Schedule UI refresh on main thread (audio thread can't touch Textual directly)
            self.call_from_thread(self._update_playhead, prev_step, self.current_step)

    def _set_playhead(self, i, visible):
        self.query_one(f"#ph_{i}", Label).update("▼" if visible else " ")

    def _update_playhead(self, prev, new):
        if prev >= 0:
            self._set_playhead(prev, False)
        self._set_playhead(new, True)

    def _update_step_button(self, i):
        button = self.query_one(f"#step_{i}", Button)
        pad, level = self.steps[i]
        button.label = LEVEL_CHARS[level]
        button.remove_class("step-off", "step-on", "step-cursor")
        if level > 0:
            button.add_class("step-on")
        else:
            button.add_class("step-off")
        if i == self.cursor_step or self.select_all:
            button.add_class("step-cursor")

    def _update_voice_cell(self, step):
        pad, level = self.steps[step]
        self.query_one(f"#voice_{step}", Label).update(str(pad + 1) if level > 0 else " ")

    def _update_voice_row(self):
        for step in range(16):
            self._update_voice_cell(step)

    def update_step_display(self):
        for i in range(16):
            self._update_step_button(i)
        self._update_voice_row()

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if not button_id:
            return
        if button_id.startswith("pad_"):
            pad_num = int(button_id.replace("pad_", ""))
            if pad_num == PLAY_PAD:
                self.toggle_play()
            elif pad_num == QUANTIZE_PAD:
                self.toggle_quantize()
            elif pad_num == SELECT_ALL_PAD:
                self.toggle_select_all()
            else:
                self.select_pad(pad_num)
                self.trigger_pad(pad_num)
        elif button_id.startswith("step_"):
            step_num = int(button_id.replace("step_", ""))
            self.toggle_step(step_num)

    def on_midi(self, msg):
        if msg.type == "note_on" and msg.velocity > 0:
            pad_num = NOTE_TO_PAD.get(msg.note)
            if pad_num == PLAY_PAD:
                self.toggle_play()
            elif pad_num == QUANTIZE_PAD:
                self.toggle_quantize()
            elif pad_num == SELECT_ALL_PAD:
                self.toggle_select_all()
            elif pad_num is not None:
                self.trigger_pad(pad_num, msg.velocity)
                self.active_pads.add(pad_num)
        elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
            pad_num = NOTE_TO_PAD.get(msg.note)
            if pad_num in self.active_pads:
                self.release_pad(pad_num)
                self.active_pads.discard(pad_num)
        elif msg.type == "control_change" and msg.control == 3:
            self.master_volume = msg.value / 127.0
            self.volume_label.update(f"Vol: {int(self.master_volume * 100)}%")
        elif msg.type == "control_change" and msg.control == 9:
            self.rand = msg.value / 127.0
            self.rand_label.update(f"Ran: {int(self.rand * 100)}%")
        elif msg.type == "control_change" and msg.control == 13:
            old = self.cursor_step
            self.cursor_step = int(msg.value * 15 / 127)
            self._update_step_button(old)
            self._update_step_button(self.cursor_step)
        elif msg.type == "control_change" and msg.control == 12:
            level = int(msg.value / 26) * 25
            if level > 100:
                level = 100
            value = (self.selected_pad, level) if level > 0 else (-1, 0)
            targets = range(16) if self.select_all else (self.cursor_step,)
            for step in targets:
                self.steps[step] = value
                self._update_step_button(step)
                self._update_voice_cell(step)
        elif msg.type == "control_change" and msg.control == 15:
            self.select_pad(int(msg.value * 15 / 127))

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
    if app.fatal_error:
        print(app.fatal_error, file=sys.stderr)
        sys.exit(1)
