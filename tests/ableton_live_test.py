import time
import threading
import showtime
from showtime import Showtime as ZST
from showtime import ZstEventCallback, ZstURI, ZstInputPlugEventCallback


class PlugCallback(ZstInputPlugEventCallback):
    def run(self, plug):
        print("Plug received value {0}".format(plug.value().float_at(0)))


class EventCallback(ZstEventCallback):
    def run(self, event):
        print("Received stage event {0} from {1}".format(
            event.get_update_type(), event.get_first().to_char()))


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

stageCallback = EventCallback()
ZST.attach_stage_event_callback(stageCallback)
ZST.join("127.0.0.1")
perf = ZST.create_performer("python_perf")

uri_out = ZstURI.create("ableton_perf", "B-B-Delay-{7}/Delay-{8}/Feedback", "out", ZstURI.OUT_JACK)
uri_in = ZstURI.create("python_perf", "ins", "plug_in", ZstURI.IN_JACK)

plug_in = ZST.create_input_plug(uri_in, showtime.ZST_INT)
ZST.connect_cable(uri_in, uri_out)
time.sleep(0.2)

plug_callback = PlugCallback()
plug_in.attach_recv_callback(plug_callback);
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
