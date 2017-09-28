import rtmidi
import platform

import showtime
from showtime import Showtime as ZST
from showtime import ZstEventCallback, ZstURI, ZstPlugDataEventCallback, ZstComponent


# class CC_Event(ZstPlugDataEventCallback):
#     def run(self, plug):
#         if plug.value().size() > 0:
#             val = plug.value().int_at(0)
#             print("Sending midi message Channel:{0} CC:{1} Val:{2}".format(self.channel, self.cc, val))
#             self.midi_out.sendMessage(rtmidi.MidiMessage.controllerEvent(self.channel, self.cc, val))

#     def set_cc_params(self, channel, cc, midi_out):
#         self.channel = channel
#         self.cc = cc
#         self.midi_out = midi_out

class CCGroup(ZstComponent):
    def __init__(self, name, parent, midiport):
        ZstComponent.__init__(self, "MidiCCGroup", name, parent)
        self.midi_out = midiport
        self.plug_cc_map = {}
        self.midi_out = midiport
        self.entities = []

    def compute(self, plug):
        if plug.size() > 0:
            if plug.get_URI().path() in self.plug_cc_map:
                plug_URI = plug.get_URI().path()
                channel = self.plug_cc_map[plug_URI][0]
                cc = self.plug_cc_map[plug_URI][1]
                val = plug.int_at(0)
                print("Sending midi message Channel:{0} CC:{1} Val:{2}".format(channel, cc, val))
                self.midi_out.sendMessage(rtmidi.MidiMessage.controllerEvent(channel, cc, val))

    def create_cc_entity(self, name, channel, cc):
        entity = CCGroup(name, self, self.midi_out)
        self.entities.append(entity)
        entity.create_cc_plug_pair(channel, cc)

    def create_cc_plug_pair(self, channel, cc):
        in_plug = self.create_input_plug("recv", showtime.ZST_INT)
        # out_plug = self.create_output_plug("{0}/send".format(name), showtime.ZST_INT)
        self.plug_cc_map[in_plug.get_URI().path()] = (channel, cc)


    def send_cc(self, channel, cc, value):
        self.midi_out.sendMessage(rtmidi.MidiMessage.controllerEvent(channel, cc, value))


class MidiPerformer(ZstComponent):
    def __init__(self, performer, midiportindex, virtual=False):
        self.groups = []
        ZstComponent.__init__(self, "MidiPerformer", performer)

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

    def create_cc_group(self, name, parent=None):
        parent = parent if parent else self
        group = CCGroup(name, parent, self.midi_out)
        self.groups.append(group)
        return group

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


if __name__ == "__main__":
    m = MidiPerformer(2)
    raw_input("pause")
    ZST.destroy()
