from __future__ import with_statement
import sys
import Live
import LiveUtils
from _Framework.ControlSurface import ControlSurface
from _Framework.EncoderElement import *

from LiveWrappers.LiveWrapper import LiveWrapper
from LiveWrappers.LiveSong import LiveSong
from LiveWrappers.LiveBrowser import LiveBrowser

from Logger import Log

import random

import showtime
from showtime import Showtime as ZST
from showtime import ZstComponent


class ShowtimeBridge(ControlSurface):
    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        with self.component_guard():
            self.cInstance = c_instance
            self._suppress_send_midi = True

            Log.set_logger(self.log_message)
            Log.set_log_level(Log.LOG_INFO)
            Log.set_log_network(False)
            Log.write("-----------------------")
            Log.write("Showtime-Live starting")
            Log.write("Python version " + sys.version)
            Log.info(sys.version)

            Log.write("Starting native showtime library")
            ZST.init()
            ZST.join("127.0.0.1")
            LiveSong.add_instance(LiveSong(LiveUtils.getSong()))
            # LiveBrowser.add_instance(LiveBrowser(Live.Application.get_application().browser))

            # Midi clock to trigger incoming message check
            self.clock = EncoderElement(msg_type=MIDI_CC_TYPE, channel=0, identifier=119, map_mode=Live.MidiMap.MapMode.absolute)

            self.refresh_state()
            self._suppress_send_midi = False

    def showtime_cleanup(self):
        ZST.destroy()

    def disconnect(self):
        self._suppress_send_midi = True
        self._suppress_send_midi = False
        self.showtime_cleanup()
        ControlSurface.disconnect(self)

    def refresh_state(self):
        ControlSurface.refresh_state(self)
        self.request_rebuild_midi_map()

    def build_midi_map(self, midi_map_handle):
        Log.info("Building midi map...")
        ControlSurface.build_midi_map(self, midi_map_handle)

    def update(self):
        self.request_loop()
        ControlSurface.update(self)

    def receive_midi(self, midi_bytes):
        # Hack to get a faster update loop. Call our update function each time we receive
        # a midi message
        self.request_loop()
        ControlSurface.receive_midi(self, midi_bytes)

    def suggest_map_mode(self, cc_no, channel):
        return Live.MidiMap.MapMode.absolute

    def update_display(self):
        # Call the request handler so that messages will always be accepted
        self.request_loop()
        ControlSurface.update_display(self)

    def request_loop(self):
        # Handle incoming Showtime events
        while(ZST.event_queue_size() > 0):
            ZST.poll_once()

        LiveWrapper.process_deferred_actions()

        # Tick the song forwards one step
        if len(LiveSong.instances()) > 0:
            LiveSong.instances()[0].tick()
