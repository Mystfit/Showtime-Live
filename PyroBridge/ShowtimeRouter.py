from Pyro.EventService.Clients import Subscriber
import Pyro.core
import Pyro.errors

import sys
sys.path.append("/Users/mystfit/Code/zmqshowtime/python")
from zst_node import ZstNode
from zst_method import ZstMethod

from LiveBridge.LiveWrappers.PyroTrack import PyroTrackActions
from LiveBridge.LiveWrappers.PyroDevice import PyroDeviceActions
from LiveBridge.LiveWrappers.PyroDeviceParameter import PyroDeviceParameterActions
from LiveBridge.LiveWrappers.PyroSong import PyroSongActions
from LiveBridge.LiveWrappers.PyroSend import PyroSendActions
from LiveBridge.LiveWrappers.PyroSendVolume import PyroSendVolumeActions

from PyroPublisher import PyroPublisher

import PyroShared


# Event listener class for recieving/parsing messages from Live
class ShowtimeRouter(Subscriber):

    def __init__(self, stageaddress, midiPort):
        Subscriber.__init__(self)
        self.setThreading(True)

        self.publisher = PyroPublisher()
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
        # Register outgoing Showtime actions
        self.node.request_register_method(
            PyroTrackActions.FIRED_SLOT_INDEX, ZstMethod.READ)
        self.node.request_register_method(
            PyroTrackActions.PLAYING_SLOT_INDEX, ZstMethod.READ)
        self.node.request_register_method(
            PyroDeviceParameterActions.VALUE_UPDATED, ZstMethod.READ)
        self.node.request_register_method(
            PyroDeviceActions.PARAMETERS_UPDATED, ZstMethod.READ)
        self.node.request_register_method(
            PyroSendVolumeActions.SEND_UPDATED, ZstMethod.READ)

        # Register outgoing Pyro actions
        outgoingActions = [
            PyroTrackActions.FIRED_SLOT_INDEX,
            PyroTrackActions.PLAYING_SLOT_INDEX,
            PyroDeviceActions.PARAMETERS_UPDATED,
            PyroDeviceParameterActions.VALUE_UPDATED,
            PyroSongActions.GET_SONG_LAYOUT,
            PyroSendVolumeActions.SEND_UPDATED
        ]

        subscribed = [
            PyroShared.OUTGOING_PREFIX + method for method in outgoingActions]
        self.subscribe(subscribed)

        # Incoming methods
        self.node.request_register_method(
            PyroSongActions.FIRE_CLIP,
            ZstMethod.WRITE,
            {
                "trackindex": None,
                "clipindex": None
            },
            self.incoming)

        self.node.request_register_method(
            PyroSongActions.STOP_TRACK,
            ZstMethod.WRITE,
            {
                "trackindex": None
            },
            self.incoming)

        self.node.request_register_method(
            PyroSongActions.SET_VALUE,
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
            PyroSongActions.SET_SEND,
            ZstMethod.WRITE,
            {
                "trackindex": None,
                "sendindex": None,
                "value": None
            },
            self.incoming)

        self.node.request_register_method(
            PyroSongActions.GET_SONG_LAYOUT,
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
        subject = event.subject[len(PyroShared.OUTGOING_PREFIX):]
        if subject in self.node.methods:
            self.node.update_local_method_by_name(subject, event.msg)
        else:
            print "Outgoing method not registered!"

    def incoming(self, message):
        print "Publishing message " + message.name
        args = message.args if message.args else {}
        self.publisher.publish_check(
            PyroShared.INCOMING_PREFIX + message.name, args)

    # Incoming actions
    # ----------------
    def play_midi_note(self, message):
        if int(message.args["state"]):
            self.midi.send_message(
                [0x90, int(message.args["note"]), int(message.args["velocity"])])
        else:
            self.midi.send_message(
                [0x80, int(message.args["note"]), 0])
