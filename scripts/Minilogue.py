import threading
import time
import math

import MidiPerformer
import showtime
from showtime import Showtime as ZST
from showtime import ZstEventCallback, ZstURI, ZstPlugDataEventCallback, ZstComponent


class Clock(threading.Thread):
    # ----
    # The clock class sends a 1ms midi CC message with an incrementing value
    # that the Live ControlSurface can use to trigger faster event updates
    # ----
    def __init__(self, midiport, target_URI):
        threading.Thread.__init__(self)
        self.exitFlag = 0
        self.setDaemon(True)
        self.clockVal = 0
        self.rate = 0.005
        self.midi_out = midiport
        self.midi_active = False
        self.entity = ZstComponent("OUTPUT", "clock")
        time.sleep(0.1)

        self.sin_out = self.entity.create_output_plug("sin", showtime.OUT_JACK)
        
        time.sleep(0.1)
        ZST.connect_cable(self.sin_out.get_URI(), target_URI)

    def stop(self):
        self.midi_active = False
        self.exitFlag = 1

    def run(self):
        while not self.exitFlag:
            if self.midi_active and self.midi_out:
                self.clockVal += 0.005
                sinval = (math.sin(self.clockVal) * 0.25 + 0.5) * 127
                # self.clockVal %= 127
                self.sin_out.value().append_int(int(sinval))
                self.sin_out.fire()
                self.sin_out.value().clear()

            ZST.poll_once()
            time.sleep(self.rate)


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
    
    # clock1 = Clock(m.midi_out, ZstURI("{0}/filter/cutoff/recv".format(synth_name)))
    # clock2 = Clock(m.midi_out, ZstURI("{0}/delay/hipass_cutoff/recv".format(synth_name)))

    # clock1.start()
    # clock1.midi_active = m.midi_active
    # clock2.start()
    # clock2.midi_active = m.midi_active
    while True:
        ZST.poll_once()
    raw_input("pause")

    # clock1.stop()
    # clock2.stop()
    m.close()
