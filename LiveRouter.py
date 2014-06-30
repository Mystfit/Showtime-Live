from Pyro.EventService.Clients import Subscriber
import Pyro.core
import Pyro.errors

import sys
sys.path.append("/Users/mystfit/Code/zmqshowtime/python")
from zst_node import ZstNode
from zst_method import ZstMethod
from LiveWrappers import *
from LivePublisher import LivePublisher
import json


# Event listener class for recieving/parsing messages from Live
class LiveRouter(Subscriber):

    def __init__(self, stageaddress, midiPort):
        Subscriber.__init__(self)
        self.setThreading(True)

        # Methods for Pyro to subscribe to
        subscribed = [
            PyroTrack.FIRED_SLOT_INDEX,
            PyroTrack.PLAYING_SLOT_INDEX,
            PyroDevice.PARAMETERS_UPDATED,
            PyroDeviceParameter.VALUE_UPDATED,
            PyroSong.GET_SONG_LAYOUT,
            PyroSendVolume.SEND_UPDATED
        ]

        subscribed = [OUTGOING_PREFIX + method for method in subscribed] 
        self.subscribe(subscribed)

        # uri = "PYRONAME://" + Pyro.constants.EVENTSERVER_NAME
        # self.publisher = Pyro.core.getProxyForURI(uri)
        self.publisher = LivePublisher()

        self.midi = midiPort

        # Create showtime node
        self.node = ZstNode("LiveNode", stageaddress)
        self.node.start()
        self.node.request_register_node()
        self.register_methods()

    def close(self):
        self.node.close()
        self.getDaemon().shutdown(True)

    def register_methods(self):
        # Outgoing methods
        self.node.request_register_method(PyroTrack.FIRED_SLOT_INDEX, ZstMethod.READ)
        self.node.request_register_method(PyroTrack.PLAYING_SLOT_INDEX, ZstMethod.READ)
        self.node.request_register_method(PyroDeviceParameter.VALUE_UPDATED, ZstMethod.READ)
        self.node.request_register_method(PyroDevice.PARAMETERS_UPDATED, ZstMethod.READ)
        self.node.request_register_method(PyroSendVolume.SEND_UPDATED, ZstMethod.READ)

        # Incoming methods
        self.node.request_register_method(
            PyroTrack.FIRE_CLIP,
            ZstMethod.WRITE,
            {
                "trackindex": None,
                "clipindex": None
            },
            self.incoming)

        self.node.request_register_method(
            PyroTrack.STOP_TRACK,
            ZstMethod.WRITE,
            {
                "trackindex": None
            },
            self.incoming)

        self.node.request_register_method(
            PyroDeviceParameter.SET_VALUE,
            ZstMethod.WRITE,
            {
                "trackindex": None,
                "deviceindex": None,
                "parameterindex": None,
                "category": None,
                "value": None
            },
            self.incoming)

        self.node.request_register_method(
            PyroSendVolume.SET_SEND,
            ZstMethod.WRITE,
            {
                "trackindex": None,
                "sendindex": None,
                "value": None
            },
            self.incoming)

        self.node.request_register_method(
            PyroSong.GET_SONG_LAYOUT,
            ZstMethod.RESPONDER, None,
            self.incoming, None)

        self.node.request_register_method(
            "play_note",
            ZstMethod.WRITE,
            {
                "trackindex": None,
                "note": None,
                "state": None,
                "velocity": None
            },
            self.play_midi_note)

    def event(self, event):
        print "IN-->OUT: " + event.subject, '=', event.msg
        subject = event.subject[len(OUTGOING_PREFIX):]
        if subject in self.node.methods:
            self.node.update_local_method_by_name(subject, event.msg)
        else:
            print "Outgoing method not registered!"

    def incoming(self, message):
        print "Publishing message " + message.name
        args = message.args if message.args else {}
        self.publisher.publish_check(INCOMING_PREFIX + message.name, args)

    def play_midi_note(self, message):
        if int(message.args["state"]):
            self.midi.send_message(
                [0x90, int(message.args["note"]), int(message.args["velocity"])])
        else:
            self.midi.send_message(
                [0x80, int(message.args["note"]), 0])
