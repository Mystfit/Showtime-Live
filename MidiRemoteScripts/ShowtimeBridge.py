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
import showtime.showtime as ZST

class JoinStageEvent(ZST.ZstSessionAdaptor):

    def __init__(self, song):
        ZST.ZstSessionAdaptor.__init__(self)
        self.song = song

    def on_connected_to_stage(self):
        try:
            Log.write("Connected to stage server")
            # LiveBrowser.add_instance(LiveBrowser(Live.Application.get_application().browser))
        except Exception as e:
            Log.error(e)


class ShowtimeBridge(ControlSurface):
    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        with self.component_guard():
            self.cInstance = c_instance
            self._suppress_send_midi = True

            # Start logging
            Log.set_logger(self.log_message)
            Log.set_log_level(Log.LOG_INFO)
            Log.set_log_network(False)


            # Showtime init
            Log.write("-----------------------")
            Log.write("Showtime-Live starting")
            Log.write("Python version " + sys.version)
            ZST.init("live", True)

            # Create top level song object
            self.song = LiveSong("song", LiveUtils.getSong())
            ZST.get_root().add_child(self.song)
            self.song.refresh_hierarchy(False)

            # Join server
            self.join_event = JoinStageEvent(self.song)
            ZST.add_session_adaptor(self.join_event)
            ZST.join_async("127.0.0.1")

            # Midi clock to trigger incoming message check
            self.clock = EncoderElement(msg_type=MIDI_CC_TYPE, channel=0, identifier=119, map_mode=Live.MidiMap.MapMode.absolute)

            self.refresh_state()
            self._suppress_send_midi = False

    def __del__(self):
        ZST.destroy()

    def disconnect(self):
        self._suppress_send_midi = True
        self._suppress_send_midi = False
        ZST.leave()
        del self.join_event
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
        ZST.poll_once()

        LiveWrapper.process_deferred_actions()

        # Tick the song forwards one step
        # if len(LiveSong.instances()) > 0:
        #     LiveSong.instances()[0].tick()
