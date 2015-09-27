from Pyro.EventService.Clients import Subscriber
import Pyro.core
import Pyro.errors

from Showtime.zst_node import ZstNode
from Showtime.zst_method import ZstMethod

import sys
import threading
import os
import Queue
sys.path.append(os.path.join(os.path.dirname(__file__), "../Midi_Remote_Scripts"))

# from ShowtimeBridge.LiveWrappers.PyroTrack import PyroTrackActions

from ShowtimeBridge.LivePublisher import LivePublisher
from ShowtimeBridge.PyroShared import PyroPrefixes
import Showtime_Live.MidiRouter


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

class LiveRouter(Subscriber):
    def __init__(self, stageaddress, midiportindex):
        Subscriber.__init__(self)
        self.setThreading(True)

        self.publisher = LivePublisher()
        self.midiRouter = Showtime_Live.MidiRouter.MidiRouter(midiportindex)

        if not self.midiRouter.midiActive():
            print("--- No midi loopback port available, incoming messages to Ableton will be considerably slower")
            print("--- Is loopMidi running?\n")

        if not stageaddress:
            print("Creating internal stage at tcp://127.0.0.1:6000")
            self.stageNode = ZstNode("ShowtimeStage")
            port = 6000
            address = "tcp://*:" + str(port)
            self.stageNode.reply.socket.bind(address)
            self.stageNode.start()
            stageaddress = "127.0.0.1:" + str(port)

        # Create showtime node
        self.node = ZstNode("LiveNode", stageaddress)
        self.node.start()
        self.node.request_register_node()
        self.register_methods()
        self.subscribeMatch('[^' + PyroPrefixes.DELIMITER + ']*')
        self.registrar = RegistrationThread(self.node)
        self.registrar.daemon = True
        self.registrar.start()

    def close(self):
        self.registrar.stop()
        self.node.close()
        if(hasattr(self, "stageNode")):
            self.stageNode.close()
        self.getDaemon().shutdown(True)
        self.midiRouter.close()

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
        # elif pyroType == PyroPrefixes.PASSTHROUGH:
        #     print "Passthrough: " + methodName
        elif pyroType == PyroPrefixes.OUTGOING:
            print "Live-->ST: " + str(event.subject) + '=' + str(event.msg)
            if methodName in self.node.methods:
                self.node.update_local_method_by_name(methodName, event.msg)
            else:
                print "Outgoing method not registered!"

    def incoming(self, message):
        print "ST-->Live: " + str(message.name)
        args = message.args if message.args else {}
        self.publisher.send_to_live(message.name, args)
