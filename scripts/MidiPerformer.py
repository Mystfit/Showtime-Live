import rtmidi
import platform

import showtime.showtime as ZST


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

class CCGroup(ZST.ZstComponent):
    def __init__(self, name, midiport, channel=-1, cc=-1):
        ZST.ZstComponent.__init__(self, "MidiCCGroup", name)
        self.midi_out = midiport
        self.plug_cc_map = {}
        self.midi_out = midiport
        self.channel = channel
        self.cc = cc
        self.owned_children = []

    def add_child(self, child, removed=False):
        ZST.ZstComponent.add_child(self, child)
        self.owned_children.append(child)

    def on_registered(self):
        self.create_cc_plug_pair(self.channel, self.cc)

    def compute(self, plug):
        if plug.size() > 0:
            if plug.URI().path() in self.plug_cc_map:
                plug_URI = plug.URI().path()
                channel = self.plug_cc_map[plug_URI][0]
                cc = self.plug_cc_map[plug_URI][1]
                val = plug.int_at(0)
                print("Sending midi message Channel:{0} CC:{1} Val:{2}".format(channel, cc, val))
                self.midi_out.sendMessage(rtmidi.MidiMessage.controllerEvent(channel, cc, val))

    def create_cc_entity(self, name, channel, cc):
        entity = CCGroup(name, self.midi_out, channel, cc)
        return entity

    def create_cc_plug_pair(self, channel, cc):
        in_plug = ZST.ZstInputPlug("to_midi", ZST.ZstValueType_IntList)
        self.add_child(in_plug)
        out_plug = ZST.ZstOutputPlug("from_midi", ZST.ZstValueType_IntList)
        self.add_child(out_plug)
        self.plug_cc_map[in_plug.URI().path()] = (channel, cc)
        self.plug_cc_map[out_plug.URI().path()] = (channel, cc)

    def send_cc(self, channel, cc, value):
        self.midi_out.sendMessage(rtmidi.MidiMessage.controllerEvent(channel, cc, value))


class MidiPerformer(object):
    def __init__(self, midiportindex, virtual=False):
        # Setup midi port 
        self.midiportindex = midiportindex
        self.midi_active = False
        if virtual:
            self.midi_out = self.create_midi(midiportindex)
        else:
            print("Opening midi port {0}".format(midiportindex))
            self.midi_out = rtmidi.MidiOut()
            self.midi_out.open_port(midiportindex)
        
        if not self.midi_out:
            return

    def create_cc_group(self, name):
        return CCGroup(name, self.midi_out)

    def set_midi_active(self, state):
        self.midi_active = state

    def is_midi_active(self):
        return self.midi_active

    def create_midi(self, midiportindex):
        # Midi startup. Try creating a virtual port. Doesn't work on Windows
        if platform.system() == "Windows":
            if len(midi_out.get_ports()) > 1:
                print("Can't open virtual midi port on windows. Using midi loopback instead.")
                return self.open_port(midiportindex)
            else:
                return None
        else:
            midi_out = rtmidi.MidiOut()
            midi_out.open_virtual_port("ShowtimeLive_Midi")
            print("Creating virtual midi port")
            self.set_midi_active(True)
        return midi_out

    def open_midi(self, midiportindex):
        midi_out = rtmidi.MidiOut()
        midi_out.openPort(midiportindex)
        self.set_midi_active(True)
        return midi_out

    def list_midi_ports(self):
        print("Available MidiOut ports:")

        ports = self.midi_out.get_ports()
        print(ports)
        # if ports:
        #     for i in ports:
        #         print("{0}:{1}".format(i, self.midi_out.getPortName(i)))
        # else:
        #     print("No midi out ports available")

    def close(self):
        self.midi_out.closePort()
