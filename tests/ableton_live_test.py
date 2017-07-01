import time
import showtime
import threading
try: 
    input = raw_input
except NameError: 
    pass

class Watcher(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)

    def run(self):
        while True:
            showtime.Showtime_poll_once()
            # event = showtime.Showtime_pop_event()
            # print("EVENT")
            # if event.event() == showtime.PlugEvent.HIT:
            #     print("Received plug hit: {0}".format(showtime.convert_to_int_plug(event.plug()).get_value()))

watch = Watcher()
watch.start()

showtime.Showtime_init()
showtime.Showtime_join("127.0.0.1")
perf = showtime.Showtime_create_performer("python_perf")

live_performer = input("Name of Live performer > ")
# live_instrument = input("Name of output Live instrument > ")
# live_plug = input("Name of output Live plug > ")

# live_uri_out = showtime.ZstURI_create(live_performer, live_instrument, live_plug, showtime.ZstURI.OUT_JACK)
# local_uri_in = showtime.ZstURI_create("python_perf", "ins", "plug_in", showtime.ZstURI.IN_JACK)
# plug_in = showtime.Showtime_create_int_plug(local_uri_in)

# showtime.Showtime_connect_plugs(local_uri_in, live_uri_out)

# time.sleep(0.1)

# input("wait")

live_instrument_in = "A-Reverb/Reverb/DecayTime"  # input("Name of input Live instrument > ")
live_plug_in = "in"  # input("Name of input Live plug > ")

local_plug_out = showtime.ZstURI_create("python_perf", "ins", "out", showtime.ZstURI.OUT_JACK)
plug_out = showtime.Showtime_create_int_plug(local_plug_out)
live_uri_in = showtime.ZstURI_create(live_performer, live_instrument_in, live_plug_in, showtime.ZstURI.IN_JACK)
showtime.Showtime_connect_cable(local_plug_out, live_uri_in)

val = 0
try:
    while True:
        time.sleep(0.001)
        val += 1
        val %= 127
        plug_out.fire(val)
except KeyboardInterrupt:
    print("Aborting...")

print("Done")
showtime.Showtime_destroy();
