import rtmidi
import platform

import showtime
from showtime import Showtime as ZST
from showtime import ZstEventCallback, ZstURI, ZstPlugDataEventCallback


class CC_Event(ZstPlugDataEventCallback):
    def run(self, plug):
        if plug.value().size() > 0:
            val = plug.value().int_at(0)
            print("Sending midi message Channel:{0} CC:{1} Val:{2}".format(self.channel, self.cc, val))
            self.midi_out.sendMessage(rtmidi.MidiMessage.controllerEvent(self.channel, self.cc, val))

    def set_cc_params(self, channel, cc, midi_out):
        self.channel = channel
        self.cc = cc
        self.midi_out = midi_out


class MidiPerformer:
    def __init__(self, performer, midiportindex, virtual=False):
        # Setup midi port 
        self.midiportindex = midiportindex
        self.midi_active = False
        if virtual:
            self.midi_out = self.create_midi(midiportindex)
        else:
            print("Opening midi port {0}".format(midiportindex))
            self.midi_out = self.open_midi(midiportindex)
        
        if not self.midi_out:
            return

        ZST.init()
        ZST.join("127.0.0.1")
        self.performer_name = performer
        self.performer = ZST.create_performer(self.performer_name)
        print("Creating performer %s" % self.performer_name)
        self.plugs = []
        self.plug_callbacks = []

    def create_cc_plug_pair(self, name, channel, cc):        
        in_callback = CC_Event()
        in_callback.set_cc_params(channel, cc, self.midi_out)
        in_plug = ZST.create_input_plug(ZstURI(self.performer_name, name, "in"), showtime.IN_JACK)
        in_plug.input_events().attach_event_callback(in_callback)
        self.plug_callbacks.append(in_callback)

    def set_midi_active(self, state):
        self.midi_active = state

    def is_midi_active(self):
        return self.midi_active

    def create_midi(self, midiportindex):
        # Midi startup. Try creating a virtual port. Doesn't work on Windows
        if platform.system() == "Windows":
            if len(midi_out.ports) > 1:
                print("Can't open virtual midi port on windows. Using midi loopback instead.")
                return self.open_midi(midiportindex)
            else:
                return None
        else:
            midi_out = rtmidi.RtMidiOut()
            midi_out.openVirtualPort("ShowtimeLive_Midi")
            print("Creating virtual midi port")
            self.set_midi_active(True)
        return midi_out

    def open_midi(self, midiportindex):
        midi_out = rtmidi.RtMidiOut()
        midi_out.openPort(midiportindex)
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
        self.midi_out.closePort()
        ZST.destroy()

    def send_cc(self, channel, cc, value):
        self.midi_out.sendMessage(rtmidi.MidiMessage.controllerEvent(channel, cc, value))


if __name__ == "__main__":
    m = MidiPerformer(2)
    raw_input("pause")
    ZST.destroy()
