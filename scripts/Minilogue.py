import threading
import time

import MidiPerformer
import showtime
from showtime import Showtime as ZST
from showtime import ZstEventCallback, ZstURI, ZstPlugDataEventCallback


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
        self.rate = 0.05
        self.midi_out = midiport
        self.midi_active = False

        self.clock_performer_name = "miniloguetest"
        self.clock_performer = ZST.create_performer(self.clock_performer_name)
        out_URI = ZstURI(self.clock_performer_name, "clock", "out")
        self.plug_out = ZST.create_output_plug(out_URI, showtime.OUT_JACK)
        time.sleep(0.2)
        ZST.connect_cable(out_URI, target_URI)

    def stop(self):
        self.midi_active = False
        self.exitFlag = 1

    def run(self):
        while not self.exitFlag and self.midi_out:
            self.clockVal += 1
            self.clockVal %= 127
            if self.midi_active:
                self.plug_out.value().append_int(self.clockVal)
                print(self.plug_out.value().int_at(0))
                self.plug_out.fire()
                self.plug_out.value().clear()
                ZST.poll_once()
            time.sleep(self.rate)


class Minilouge(MidiPerformer.MidiPerformer):
    def __init__(self, synth_name, midiportindex):
        MidiPerformer.MidiPerformer.__init__(self, synth_name, midiportindex)
        self.create_plugs()

    def create_plugs(self):
        channel = 1
        self.create_cc_plug_pair("amp EG/attack",           channel, 16)
        self.create_cc_plug_pair("amp EG/decay",            channel, 17)
        self.create_cc_plug_pair("amp EG/sustain",          channel, 18)
        self.create_cc_plug_pair("amp EG/release",          channel, 19)
        self.create_cc_plug_pair("EG/attack",               channel, 20)
        self.create_cc_plug_pair("EG/decay",                channel, 21)
        self.create_cc_plug_pair("EG/sustain",              channel, 22)
        self.create_cc_plug_pair("EG/release",              channel, 23)
        self.create_cc_plug_pair("LFO/rate",                channel, 24)
        self.create_cc_plug_pair("LFO/depth",               channel, 26)
        self.create_cc_plug_pair("LFO/target",              channel, 56)
        self.create_cc_plug_pair("LFO/eg mod",              channel, 57)
        self.create_cc_plug_pair("LFO/wave",                channel, 58)
        self.create_cc_plug_pair("voice depth",             channel, 27)
        self.create_cc_plug_pair("delay/hipass",            channel, 29)
        self.create_cc_plug_pair("delay/time",              channel, 30)
        self.create_cc_plug_pair("delay/feedback",          channel, 31)
        self.create_cc_plug_pair("VCO1/octave",             channel, 48)
        self.create_cc_plug_pair("VCO1/wave",               channel, 50)
        self.create_cc_plug_pair("VCO1/pitch",              channel, 34)
        self.create_cc_plug_pair("VCO1/shape",              channel, 36)
        self.create_cc_plug_pair("VCO2/octave",             channel, 49)
        self.create_cc_plug_pair("VCO2/wave",               channel, 51)
        self.create_cc_plug_pair("VCO2/pitch",              channel, 35)
        self.create_cc_plug_pair("VCO2/shape",              channel, 37)
        self.create_cc_plug_pair("VCO2/modulation/cross mod depth",    channel, 41)
        self.create_cc_plug_pair("VCO2/modulation/pitch eg int",       channel, 42)
        self.create_cc_plug_pair("VCO2/modulation/sync",               channel, 80)
        self.create_cc_plug_pair("VCO2/modulation/ring",               channel, 81)
        self.create_cc_plug_pair("mixer/VCO1 level",              channel, 33)
        self.create_cc_plug_pair("mixer/VCO2 level",              channel, 39)
        self.create_cc_plug_pair("mixer/noise level",             channel, 40)
        self.create_cc_plug_pair("filter/cutoff",           channel, 11) #43
        self.create_cc_plug_pair("filter/resonance",        channel, 44)
        self.create_cc_plug_pair("filter/eg int",           channel, 45)
        self.create_cc_plug_pair("filter/keytrack",           channel, 82)
        self.create_cc_plug_pair("filter/velocity",           channel, 83)


if __name__ == "__main__":

    synth_name = "minilogue"
    m = Minilouge(synth_name, 1)
    clock = Clock(m.midi_out, ZstURI(synth_name, "filter/cutoff", "in"))
    clock.start()
    clock.midi_active = m.midi_active
    raw_input("pause")

    clock.stop()
    m.close()
