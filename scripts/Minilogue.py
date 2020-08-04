import threading
import time
import math

import MidiPerformer
import showtime.showtime as ZST

class Minilouge(MidiPerformer.MidiPerformer):
    def __init__(self, client, midiportindex):
        MidiPerformer.MidiPerformer.__init__(self, midiportindex)
        self.client = client
        time.sleep(1)
        self.create_plugs()

    def create_plugs(self):
        channel = 1
        root = self.client.get_root()
        self.amp_EG = self.create_cc_group("amp_EG")
        root.add_child(self.amp_EG)
        self.amp_EG.add_child(self.amp_EG.create_cc_entity("attack", channel, 16))
        self.amp_EG.add_child(self.amp_EG.create_cc_entity("decay", channel, 17))
        self.amp_EG.add_child(self.amp_EG.create_cc_entity("sustain", channel, 18))
        self.amp_EG.add_child(self.amp_EG.create_cc_entity("release", channel, 19))

        self.EG = self.create_cc_group("EG")
        root.add_child(self.EG)
        self.EG.add_child(self.EG.create_cc_entity("attack", channel, 20))
        self.EG.add_child(self.EG.create_cc_entity("decay", channel, 21))
        self.EG.add_child(self.EG.create_cc_entity("sustain", channel, 22))
        self.EG.add_child(self.EG.create_cc_entity("release", channel, 23))

        self.LFO = self.create_cc_group("LFO")
        root.add_child(self.LFO)
        self.LFO.add_child(self.LFO.create_cc_entity("rate", channel, 24))
        self.LFO.add_child(self.LFO.create_cc_entity("depth", channel, 26))
        self.LFO.add_child(self.LFO.create_cc_entity("target", channel, 56))
        self.LFO.add_child(self.LFO.create_cc_entity("eg_mod", channel, 57))
        self.LFO.add_child(self.LFO.create_cc_entity("wave", channel, 58))
        
        self.general = self.create_cc_group("general")
        root.add_child(self.general)
        self.general.add_child(self.general.create_cc_entity("voice depth", channel, 27))

        self.delay = self.create_cc_group("delay")
        root.add_child(self.delay)
        self.delay.add_child(self.delay.create_cc_entity("hipass_cutoff", channel, 29))
        self.delay.add_child(self.delay.create_cc_entity("time", channel, 30))
        self.delay.add_child(self.delay.create_cc_entity("feedback", channel, 31))

        self.VCO1 = self.create_cc_group("VCO1")
        root.add_child(self.VCO1)
        self.VCO1.add_child(self.VCO1.create_cc_entity("octave", channel, 48))
        self.VCO1.add_child(self.VCO1.create_cc_entity("wave", channel, 50))
        self.VCO1.add_child(self.VCO1.create_cc_entity("pitch", channel, 34))
        self.VCO1.add_child(self.VCO1.create_cc_entity("shape", channel, 36))

        self.VCO2 = self.create_cc_group("VCO2")
        root.add_child(self.VCO2)
        self.VCO2.add_child(self.VCO2.create_cc_entity("octave", channel, 49))
        self.VCO2.add_child(self.VCO2.create_cc_entity("wave", channel, 51))
        self.VCO2.add_child(self.VCO2.create_cc_entity("pitch", channel, 35))
        self.VCO2.add_child(self.VCO2.create_cc_entity("shape", channel, 37))

        self.VCO2_modulation = self.create_cc_group("modulation")
        self.VCO2.add_child(self.VCO2_modulation)
        self.VCO2_modulation.add_child(self.VCO2_modulation.create_cc_entity("cross_mod_depth", channel, 41))
        self.VCO2_modulation.add_child(self.VCO2_modulation.create_cc_entity("pitch_eg_int", channel, 42))
        self.VCO2_modulation.add_child(self.VCO2_modulation.create_cc_entity("sync", channel, 80))
        self.VCO2_modulation.add_child(self.VCO2_modulation.create_cc_entity("ring", channel, 81))

        self.mixer = self.create_cc_group("mixer")
        root.add_child(self.mixer)
        self.mixer.add_child(self.mixer.create_cc_entity("VCO1_level", channel, 33))
        self.mixer.add_child(self.mixer.create_cc_entity("VCO2_level", channel, 39))
        self.mixer.add_child(self.mixer.create_cc_entity("noise_level", channel, 40))

        self.filter = self.create_cc_group("filter")
        root.add_child(self.filter)
        self.filter.add_child(self.filter.create_cc_entity("cutoff", channel, 11))
        self.filter.add_child(self.filter.create_cc_entity("resonance", channel, 12))
        self.filter.add_child(self.filter.create_cc_entity("eg_int", channel, 13))
        self.filter.add_child(self.filter.create_cc_entity("keytrack", channel, 83))
        self.filter.add_child(self.filter.create_cc_entity("velocity", channel, 82))


if __name__ == "__main__":
    client = ZST.ShowtimeClient()
    client.init("Minilogue", True)
    client.auto_join_by_name("stage")

    m = Minilouge(client, 0)
    m.list_midi_ports()
    time.sleep(0.1)

    while True:
        client.poll_once()
    raw_input("pause")
    m.close()
