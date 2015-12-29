from __future__ import with_statement

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "ext_libs"))

import encodings

# Import Live libraries
import Live
from _Framework.ControlSurface import ControlSurface
from _Framework.EncoderElement import EncoderElement

# Import custom live objects
from LiveUtils import *
from ControlSurfaceComponents import *
from ControlSurfaceComponents.LoopingEncoderElement import LoopingEncoderElement

from LiveWrappers.LiveWrapper import LiveWrapper
from LiveWrappers.LiveDevice import LiveDevice
from LiveWrappers.LiveDeviceParameter import LiveDeviceParameter
from LiveWrappers.LiveSend import LiveSend
from LiveWrappers.LiveSong import LiveSong
from LiveWrappers.LiveTrack import LiveTrack

from LiveNetworkEndpoint import LiveNetworkEndpoint
from Logger import Log


class ShowtimeBridge(ControlSurface):
    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        with self.component_guard():
            self.cInstance = c_instance
            self._suppress_send_midi = True

            Log.set_logger(self.log_message)
            Log.set_log_level(Log.LOG_WARN)
            Log.set_log_network(True)
            Log.write("-----------------------")
            Log.write("ShowtimeBridge starting")
            Log.write("Python version " + sys.version)
            Log.info(sys.version)

            self.initServer()

            # Midi clock to trigger incoming message check
            self.clock = LoopingEncoderElement(0, 119)

            self.refresh_state()
            self._suppress_send_midi = False

    def initServer(self):
        self.endpoint = LiveNetworkEndpoint()
        LiveWrapper.set_endpoint(self.endpoint)

    def disconnect(self):
        self._suppress_send_midi = True
        self._suppress_send_midi = False
        self.endpoint.close()
        ControlSurface.disconnect(self)

    def refresh_state(self):
        ControlSurface.refresh_state(self)
        self.request_rebuild_midi_map()

    def build_midi_map(self, midi_map_handle):
        Log.info("Building midi map...")
        ControlSurface.build_midi_map(self, midi_map_handle)

    def receive_midi(self, midi_bytes):
        # Hack to get a faster update loop. Call our update function each time we receive
        # a midi message
        self.requestLoop()
        ControlSurface.receive_midi(self, midi_bytes)

    def suggest_map_mode(self, cc_no, channel):
        return Live.MidiMap.MapMode.absolute

    def update_display(self):
        #Call the request handler so that messages will always be accepted
        self.requestLoop()
        ControlSurface.update_display(self)

    def requestLoop(self):
        self.endpoint.poll()
        LiveWrapper.process_deferred_actions()

