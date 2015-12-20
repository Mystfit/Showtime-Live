import rtmidi_python as rtmidi
import threading
import time
import platform


class Clock(threading.Thread):
    # ----
    # The clock class sends a 1ms midi CC message with an incrementing value
    # that the Live ControlSurface can use to trigger faster event updates
    # ----
    def __init__(self, midiPort):
        threading.Thread.__init__(self)
        self.exitFlag = 0
        self.setDaemon(True)
        self.clockVal = 0
        self.rate = 0.001
        self.midi_out = midiPort
        self.midi_active = False

    def stop(self):
        self.midi_active = False
        self.exitFlag = 1

    def run(self):
        while not self.exitFlag and self.midi_out:
            self.clockVal += 1
            self.clockVal = self.clockVal % 127
            if self.midi_active:
                self.midi_out.send_message([0xB0, 119, self.clockVal])
            time.sleep(self.rate)


class MidiRouter:

    NOTE_ON = 0x90
    NOTE_OFF = 0x80

    def __init__(self, midiportindex):
        # Setup midi port 
        self.midiportindex = midiportindex
        self.midi_active = False
        self.midi_out = self.createMidi(midiportindex)

        if not self.midi_out:
            return

        # Set up midi clock
        self.clock = Clock(self.midi_out)
        self.clock.start()
        self.clock.midi_active = self.midi_active

        # Note tracking
        self.activeNotes = {}
        self.lastNote = None
        self.isMonophonic = True

    def set_midi_active(self, state):
        self.midi_active = state
        if hasattr(self, "clock"):
            print "Clock found!"
            self.clock.midi_active = state

    def midiActive(self):
        return self.midi_active

    def createMidi(self, midiportindex):
        # Midi startup. Try creating a virtual port. Doesn't work on Windows
        midi_out = rtmidi.MidiOut()

        if midiportindex:
            if platform.system() == "Windows":
                if len(midi_out.ports) > 1:
                    print "Can't open virtual midi port on windows. Using midi loopback instead."
                    midi_out.open_port(midiportindex)
                    self.set_midi_active(True)
                else:
                    return None
            else:
                midi_out.open_virtual_port("LiveShowtime_Midi")
                self.set_midi_active(True)
        return midi_out

    def listMidiPorts(self):
        print("Available MidiOut ports:")
        for portindex, port in enumerate(self.midi_out.ports):
            print str(portindex) + ": " + str(port)

    def close(self):
        self.clock.stop()
        self.midi_out.close_port()

    def play_midi_note(self, message):
        trigger = MidiRouter.NOTE_ON
        velocity = int(message.args["velocity"])
        note = int(message.args["note"])

        if note in self.activeNotes:
            if self.activeNotes[note]:
                trigger = MidiRouter.NOTE_OFF
                self.activeNotes[note] = False
                velocity = 0
            else:
                self.activeNotes[note] = True

        if self.lastNote and self.isMonophonic and self.lastNote != note:
            self.activeNotes[note] = False
            self.midi_out.send_message([MidiRouter.NOTE_OFF, self.lastNote, 0])

        self.lastNote = note
        self.midi_out.send_message([trigger, int(message.args["note"]), velocity])

if __name__ == "__main__":
    m = MidiRouter(1)
    # m.close()