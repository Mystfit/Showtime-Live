import time
import showtime
import threading

class Watcher(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)

    def run(self):
        while True:
            event = showtime.Showtime_pop_plug_event()
            if event.event() == showtime.PlugEvent.HIT:
                print("Received plug hit: {0}".format(showtime.convert_to_int_plug(event.plug()).get_value()))

watch = Watcher()
watch.start()

showtime.Showtime_init();
showtime.Showtime_join("127.0.0.1")
perf = showtime.Showtime_create_performer("python_perf")

live_uri_out = showtime.ZstURI_create("ableton_perf", "ins", "plug_out", showtime.ZstURI.OUT_JACK)
local_uri_in = showtime.ZstURI_create("python_perf", "ins", "plug_in", showtime.ZstURI.IN_JACK)
plug_in = showtime.Showtime_create_int_plug(local_uri_in)

showtime.Showtime_connect_plugs(local_uri_in, live_uri_out)
time.sleep(0.1)

# Listen test
choice = input("Listen for Live? y/n")
if choice == "y":
    try:
        while watch.runcount > 0:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Aborting...")

print("Done")
showtime.Showtime_destroy();
