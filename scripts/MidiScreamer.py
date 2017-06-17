#!python

import Showtime_Live.MidiRouter
import time

if __name__ == "__main__":
    live_midi_hack = Showtime_Live.MidiRouter.MidiRouter(0)
    try:
        while 1:
            time.sleep(1)
    except KeyboardInterrupt:
        live_midi_hack.close()
