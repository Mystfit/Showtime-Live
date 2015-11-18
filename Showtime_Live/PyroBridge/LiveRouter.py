import sys, threading, os, Queue
sys.path.append(os.path.join(os.path.dirname(__file__), "../Midi_Remote_Scripts"))

from Showtime.zst_node import ZstNode
from Showtime.zst_stage import ZstStage
from Showtime.zst_method import ZstMethod
from ShowtimeBridge.PyroShared import PyroPrefixes
from ShowtimeBridge.UDPEndpoint import UDPEndpoint, SimpleMessage

import Showtime_Live.MidiRouter
from zeroconf import ServiceBrowser, ServiceInfo, Zeroconf


class RegistrationThread(threading.Thread):
    def __init__(self, node):
        threading.Thread.__init__(self)
        self.name = "zst_registrar"
        self.exitFlag = 0
        self.node = node
        self.queued_registrations = Queue.Queue()

    def add_registration_request(self, *args):
        self.queued_registrations.put(args)

    def stop(self):
        self.exitFlag = 1

    def run(self):
        while not self.exitFlag:
            req = self.queued_registrations.get(True)
            self.node.request_register_method(req[0], req[1], req[2], req[3])
        self.join(2)

class LiveRouter(UDPEndpoint):

    def __init__(self, stageaddress, midiportindex):
        UDPEndpoint.__init__(self, 6001, 6002)
        self.midiRouter = Showtime_Live.MidiRouter.MidiRouter(midiportindex)

        if not self.midiRouter.midiActive():
            print("--- No midi loopback port available, incoming messages to Ableton will be considerably slower")
            print("--- Is loopMidi running?\n")

        if not stageaddress:
            print("Creating internal stage at tcp://127.0.0.1:6000")
            port = 6000
            self.stageNode = ZstStage("ShowtimeStage", port)
            self.stageNode.start()
            stageaddress = "127.0.0.1:" + str(port)

        # Create showtime node
        self.node = ZstNode("LiveNode", stageaddress)
        self.node.start()
        self.node.request_register_node()
        self.register_methods()
        self.registrar = RegistrationThread(self.node)
        self.registrar.daemon = True
        self.registrar.start()

    def close(self):
        self.registrar.stop()
        self.node.close()
        if(hasattr(self, "stageNode")):
            self.stageNode.close()
        self.midiRouter.close()
        UDPEndpoint.close(self)

    def register_methods(self):
        if(self.midiRouter.midiActive()):
            self.node.request_register_method(
                "play_note",
                ZstMethod.WRITE,
                {
                    "trackindex": None,
                    "note": None,
                    "state": None,
                    "velocity": None
                },
                self.midiRouter.play_midi_note)

    def event(self, event):
        methodName = event.subject[2:]
        pyroType = event.subject[:1]

        if pyroType == PyroPrefixes.REGISTRATION:
            self.registrar.add_registration_request(methodName, event.msg["methodaccess"], event.msg["args"], self.incoming)
        elif pyroType == PyroPrefixes.OUTGOING or pyroType == PyroPrefixes.RESPONDER:
            # print "Live-->ST: " + str(event.subject) + '=' + str(event.msg)
            if methodName in self.node.methods:
                self.node.update_local_method_by_name(methodName, event.msg)
            else:
                print "Outgoing method not registered!"

    def incoming(self, message):
        # print "ST-->Live: " + str(message.name)
        args = message.args if message.args else {}
        self.send_to_live(message.name, args)

    def send_to_live(self, message, args):
        return self.send_msg(SimpleMessage(PyroPrefixes.prefix_incoming(message), args))
