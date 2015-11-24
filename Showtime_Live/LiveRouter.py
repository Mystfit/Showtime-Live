import sys, threading, os, Queue, time
sys.path.append(os.path.join(os.path.dirname(__file__), "Midi_Remote_Scripts"))

from Showtime.zst_node import ZstNode
from Showtime.zst_stage import ZstStage
from Showtime.zst_method import ZstMethod
from ShowtimeBridge.NetworkEndpoint import SimpleMessage, NetworkPrefixes
from ShowtimeBridge.UDPEndpoint import UDPEndpoint
from ShowtimeBridge.TCPEndpoint import TCPEndpoint

import MidiRouter
from zeroconf import ServiceBrowser, ServiceInfo, Zeroconf


class RegistrationThread(threading.Thread):
    def __init__(self, node):
        threading.Thread.__init__(self)
        self.name = "zst_registrar"
        self.exitFlag = 0
        self.daemon = True

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
        self.join(1)


class LiveRouter(threading.Thread):
    def __init__(self, stageaddress, midiportindex):
        threading.Thread.__init__(self)
        self.name = "LiveRouter"
        self.exitFlag = 0
        self.daemon = True

        self.midiRouter = MidiRouter.MidiRouter(midiportindex)
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

        # Create registration thread
        self.register_methods()
        self.registrar = RegistrationThread(self.node)
        self.registrar.daemon = True
        self.registrar.start()

        # Create sockets
        self.tcpEndpoint = TCPEndpoint(6003, 6004, True)
        self.udpEndpoint = UDPEndpoint(6001, 6002, True)
        self.tcpEndpoint.add_event_callback(self.event)
        self.udpEndpoint.add_event_callback(self.event)
        self.tcpEndpoint.start()
        self.udpEndpoint.start()

    def run(self):
        while not self.exitFlag:
            time.sleep(1)
            self.ensure_server_available()
        self.join(1)

    def stop(self):
        self.exitFlag = 1

    def close(self):
        self.registrar.stop()
        self.node.close()
        if(hasattr(self, "stageNode")):
            self.stageNode.close()
        self.midiRouter.close()
        self.tcpEndpoint.close()
        self.udpEndpoint.close()

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
        msgType = event.subject[:1]        

        if msgType == NetworkPrefixes.REGISTRATION:
            self.registrar.add_registration_request(methodName, event.msg["methodaccess"], event.msg["args"], self.incoming)
        elif msgType == NetworkPrefixes.OUTGOING or msgType == NetworkPrefixes.RESPONDER:
            # print "Live-->ST: " + str(event.subject) + '=' + str(event.msg)
            if methodName in self.node.methods:
                self.node.update_local_method_by_name(methodName, event.msg)
            else:
                print "Outgoing method not registered!"

    def ensure_server_available(self):
        if self.udpEndpoint.peerConnected and not self.tcpEndpoint.peerConnected:
            print("Heartbeat found! Reconnecting TCP to " + str(self.tcpEndpoint.remoteAddr))
            if self.tcpEndpoint.connect():
                print("Reconnected to peer")
            else:
                print("TCP not up yet!")

        if not self.udpEndpoint.peerConnected and self.tcpEndpoint.peerConnected:
            print("Heartbeat lost")
            self.tcpEndpoint.peerConnected = False

    def incoming(self, message):
        # print "ST-->Live: " + str(message.name)
        args = message.args if message.args else {}
        self.send_to_live(message.name, args)

    def send_to_live(self, message, args):
        return self.send_msg(SimpleMessage(NetworkPrefixes.prefix_incoming(message), args))
