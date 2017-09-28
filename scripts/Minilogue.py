import threading
import time
import math

import MidiPerformer
import showtime
from showtime import Showtime as ZST
from showtime import ZstEventCallback, ZstURI, ZstPlugDataEventCallback, ZstComponent


class Minilouge(MidiPerformer.MidiPerformer):
    def __init__(self, synth_name, midiportindex):
        MidiPerformer.MidiPerformer.__init__(self, synth_name, midiportindex)
        time.sleep(1)
        self.create_plugs()

    def create_plugs(self):
        channel = 1
        self.amp_EG = self.create_cc_group("amp_EG")
        self.amp_EG.create_cc_entity("attack", channel, 16)
        self.amp_EG.create_cc_entity("decay", channel, 17)
        self.amp_EG.create_cc_entity("sustain", channel, 18)
        self.amp_EG.create_cc_entity("release", channel, 19)

        self.EG = self.create_cc_group("EG")
        self.EG.create_cc_entity("attack", channel, 20)
        self.EG.create_cc_entity("decay", channel, 21)
        self.EG.create_cc_entity("sustain", channel, 22)
        self.EG.create_cc_entity("release", channel, 23)

        self.LFO = self.create_cc_group("LFO")
        self.LFO.create_cc_entity("rate", channel, 24)
        self.LFO.create_cc_entity("depth", channel, 26)
        self.LFO.create_cc_entity("target", channel, 56)
        self.LFO.create_cc_entity("eg_mod", channel, 57)
        self.LFO.create_cc_entity("wave", channel, 58)

        self.general = self.create_cc_group("general")
        self.general.create_cc_entity("voice depth", channel, 27)

        self.delay = self.create_cc_group("delay")
        self.delay.create_cc_entity("hipass_cutoff", channel, 29)
        self.delay.create_cc_entity("time", channel, 30)
        self.delay.create_cc_entity("feedback", channel, 31)

        self.VCO1 = self.create_cc_group("VCO1")
        self.VCO1.create_cc_entity("octave", channel, 48)
        self.VCO1.create_cc_entity("wave", channel, 50)
        self.VCO1.create_cc_entity("pitch", channel, 34)
        self.VCO1.create_cc_entity("shape", channel, 36)

        self.VCO2 = self.create_cc_group("VCO2")
        self.VCO2.create_cc_entity("octave", channel, 49)
        self.VCO2.create_cc_entity("wave", channel, 51)
        self.VCO2.create_cc_entity("pitch", channel, 35)
        self.VCO2.create_cc_entity("shape", channel, 37)

        self.VCO2_modulation = self.create_cc_group("modulation", self.VCO2)
        self.VCO2_modulation.create_cc_entity("cross_mod_depth", channel, 41)
        self.VCO2_modulation.create_cc_entity("pitch_eg_int", channel, 42)
        self.VCO2_modulation.create_cc_entity("sync", channel, 80)
        self.VCO2_modulation.create_cc_entity("ring", channel, 81)

        self.mixer = self.create_cc_group("mixer")
        self.mixer.create_cc_entity("VCO1_level", channel, 33)
        self.mixer.create_cc_entity("VCO2_level", channel, 39)
        self.mixer.create_cc_entity("noise_level", channel, 40)

        self.filter = self.create_cc_group("filter")
        self.filter.create_cc_entity("cutoff", channel, 11)
        self.filter.create_cc_entity("resonance", channel, 12)
        self.filter.create_cc_entity("eg_int", channel, 13)
        self.filter.create_cc_entity("keytrack", channel, 83)
        self.filter.create_cc_entity("velocity", channel, 82)


if __name__ == "__main__":
    ZST.init()
    ZST.join("127.0.0.1")

    synth_name = "minilogue"
    m = Minilouge(synth_name, 1)
    time.sleep(0.1)

    while True:
        ZST.poll_once()
    raw_input("pause")
    m.close()
