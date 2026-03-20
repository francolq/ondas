import mido

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def note_name(note):
    octave = (note // 12) - 1
    name = NOTE_NAMES[note % 12]
    return f"{name}{octave}"

def main():
    print("Available MIDI input devices:")
    inputs = mido.get_input_names()
    if not inputs:
        print("  No devices found.")
        return
    
    for i, name in enumerate(inputs):
        print(f"  [{i}] {name}")
    
    if len(inputs) == 1:
        port_name = inputs[0]
    else:
        choice = input("\nSelect device index (or press Enter for first): ").strip()
        if choice == "":
            port_name = inputs[0]
        else:
            port_name = inputs[int(choice)]
    
    print(f"\nListening on: {port_name}")
    print("Press Ctrl+C to exit\n")
    
    with mido.open_input(port_name) as inport:
        for msg in inport:
            if msg.type == 'note_on' and msg.velocity > 0:
                print(f"Note On:  {note_name(msg.note):4s}  velocity={msg.velocity}")
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                print(f"Note Off: {note_name(msg.note):4s}")
            elif msg.type == 'control_change':
                print(f"CC: controller={msg.control} value={msg.value}")
            elif msg.type == 'pitchwheel':
                print(f"Pitch Wheel: {msg.pitch}")

if __name__ == "__main__":
    main()
