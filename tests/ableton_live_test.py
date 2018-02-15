import time
import sys
import math
import threading
import showtime as ZST
from showtime import ZstComponent, AddFilter, ZstURI, ZstComponentEvent


class ComponentArriveEvent(ZstComponentEvent):
    def run_with_component(self, target):
        print("ARRIVING: Received {}".format(target.URI().path()))


class PushComponent(ZstComponent):
    def __init__(self, name):
        ZstComponent.__init__(self, name)
        self.out = self.create_output_plug("out", ZST.ZST_FLOAT)

    def send(self, val):
        self.out.append_float(val)
        self.out.fire()


class SinkComponent(ZstComponent):
    def __init__(self, name):
        ZstComponent.__init__(self, name)
        self.input = self.create_input_plug("in", ZST.ZST_FLOAT)

    def compute(self, plug):
        print("Val: {0}".format(plug.float_at(0)))


class Watcher(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)

    def run(self):
        while True:
            ZST.poll_once()
            time.sleep(0.001)


watch = Watcher()
watch.start()

ZST.init("ableton_tester", True)

component_arrive = ComponentArriveEvent()
ZST.attach_component_event_listener(component_arrive, ZST.ARRIVING)
ZST.join("127.0.0.1")

push = PushComponent("push")
sink = SinkComponent("sink")
ZST.activate_entity(push)
ZST.activate_entity(sink)

in_plug_address = ZstURI("live/song/tracks/1-MIDI/devices/Backbeat Room/parameters/Snare/in")
out_plug_address = ZstURI("live/song/tracks/1-MIDI/devices/Backbeat Room/parameters/Snare b/out")

input_ent = ZST.find_entity(in_plug_address)
output_ent = ZST.find_entity(out_plug_address)

print(input_ent)
print(output_ent)

input_plug = ZST.cast_to_plug(input_ent)
output_plug = ZST.cast_to_plug(output_ent)

print(input_plug)
print(output_plug)

ZST.connect_cable(input_plug, push.out)
ZST.connect_cable(sink.input, output_plug)
print("Cables connected")

time.sleep(1)

# Send test value
push.send(1.0)

raw_input("Press any key to exit...\n")

ZST.destroy()
