import time
import threading
import 
from showtime import ZstFilter, ZstComponent, AddFilter
from showtime import Showtime as ZST


class PushComponent(ZstComponent):
    def __init__(self, name, parent):
        ZstComponent.__init__(self, "OUTPUT", name, parent)
        self.activate()
        self.plug = self.create_output_plug("out", showtime.ZST_INT)

    def send(self, val):
        self.plug.append_int(val)
        self.plug.fire()

class Watcher(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)

    def run(self):
        while True:
            if ZST.event_queue_size() > 0:
                ZST.poll_once()

watch = Watcher()
watch.start()

ZST.init()
ZST.join("127.0.0.1")
perf = ZST.create_performer("python_perf")

uri_out = ZstURI("ableton_perf/B-B-Delay-{7}/Delay-{8}/Feedback/out", ZstURI.OUT_JACK)
uri_in = ZstURI.create("python_perf", "ins", "plug_in", ZstURI.IN_JACK)

plug_in = ZST.create_input_plug(uri_in, showtime.ZST_INT)
ZST.connect_cable(uri_in, uri_out)
time.sleep(0.2)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass

print("Done")
ZST.remove_stage_event_callback(stageCallback)
plug_in.destroy_recv_callback(plug_callback)

ZST.destroy()
