import rtmidi
import threading
import time
import platform


class Clock(threading.Thread):
    # ----
    # The clock class sends a 1ms midi CC message with an incrementing value
    # that the Live ControlSurface can use to trigger faster event updates
    # ----
    def __init__(self, midiport):
        threading.Thread.__init__(self)
        self.exitFlag = 0
        self.setDaemon(True)
        self.clockVal = 0
        self.rate = 0.001
        self.midi_out = midiport
        self.midi_active = False

    def stop(self):
        self.midi_active = False
        self.exitFlag = 1

    def run(self):
        while not self.exitFlag and self.midi_out:
            self.clockVal += 1
            self.clockVal %= 127
            if self.midi_active:
                self.midi_out.sendMessage(rtmidi.MidiMessage.controllerEvent(1, 119, self.clockVal))
            time.sleep(self.rate)


class MidiScreamer:
    NOTE_ON = 0x90
    NOTE_OFF = 0x80

    def __init__(self, midiportindex):
        # Setup midi port 
        self.midiportindex = midiportindex
        self.midi_active = False
        self.midi_out = self.create_midi(midiportindex)

        if not self.midi_out:
            return

        # Set up midi clock
        self.clock = Clock(self.midi_out)
        self.clock.start()
        self.clock.midi_active = self.midi_active

    def set_midi_active(self, state):
        self.midi_active = state
        if hasattr(self, "clock"):
            print("Clock found!")
            self.clock.midi_active = state

    def is_midi_active(self):
        return self.midi_active

    def create_midi(self, midiportindex):
        # Midi startup. Try creating a virtual port. Doesn't work on Windows
        midi_out = rtmidi.RtMidiOut()

        if platform.system() == "Windows":
            if len(midi_out.ports) > 1:
                print("Can't open virtual midi port on windows. Using midi loopback instead.")
                midi_out.openPort(midiportindex)
                self.set_midi_active(True)
            else:
                return None
        else:
            midi_out.openVirtualPort("ShowtimeLive_Midi")
            print("Creating virtual midi port")
            self.set_midi_active(True)
        return midi_out

    def list_midi_ports(self):
        print("Available MidiOut ports:")

        ports = range(self.midi_out.getPortCount())
        if ports:
            for i in ports:
                print("{0}:{1}".format(i, self.midi_out.getPortName(i)))
        else:
            print("No midi out ports available")

    def close(self):
        self.clock.stop()
        self.midi_out.closePort()

if __name__ == "__main__":
    m = MidiRouter(1)
    try:
        while 1:
            time.sleep(1)
    except KeyboardInterrupt:
        m.close()
