import threading
import time
import math

import showtime
from showtime import Showtime as ZST
from showtime import ZstEventCallback, ZstURI, ZstPlugDataEventCallback, ZstComponent, AddFilter


class SineOutput(threading.Thread):
    # ----
    # The clock class sends a 1ms midi CC message with an incrementing value
    # that the Live ControlSurface can use to trigger faster event updates
    # ----
    def __init__(self, name, target_URI, speed):
        threading.Thread.__init__(self)
        self.exitFlag = 0
        self.setDaemon(True)
        self.clockVal = 0
        self.rate = speed
        self.entity = ZstComponent("OUTPUT", name)
        time.sleep(0.1)

        self.sin_out = self.entity.create_output_plug("sin", showtime.OUT_JACK)
        
        time.sleep(0.1)
        # ZST.connect_cable(self.sin_out.get_URI(), target_URI)

    def stop(self):
        self.midi_active = False
        self.exitFlag = 1

    def run(self):
        while not self.exitFlag:
            self.clockVal += 0.005
            sinval = (math.sin(self.clockVal) * 0.25 + 0.25) * 127
            # self.clockVal %= 127
            self.sin_out.value().append_int(int(sinval))
            print(sinval)
            self.sin_out.fire()
            self.sin_out.value().clear()

            ZST.poll_once()
            time.sleep(self.rate)


ZST.init()
ZST.join("1.1.1.5")

synth_name = "minilogue"
time.sleep(0.1)

sin1 = SineOutput("sin1", ZstURI("{0}/filter/cutoff/recv".format(synth_name)), 0.005)
sin2 = SineOutput("sin2", ZstURI("{0}/delay/hipass_cutoff/recv".format(synth_name)), 0.010)
sin3 = SineOutput("sin3", ZstURI("{0}/filter/resonance/recv".format(synth_name)), 0.010)

root = ZstComponent("ROOT", __file__)
add = AddFilter(root)

ZST.connect_cable(sin1.sin_out.get_URI(), add.augend().get_URI())
ZST.connect_cable(sin2.sin_out.get_URI(), add.addend().get_URI())
ZST.connect_cable(add.sum().get_URI(), ZstURI("{0}/filter/cutoff/recv".format(synth_name)))

sin1.start()
sin2.start()
sin3.start()

try:
    while True:
        ZST.poll_once()
except KeyboardInterrupt:
    pass

sin1.stop()
sin2.stop()
sin3.stop()

ZST.destroy()