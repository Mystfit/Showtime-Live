from __future__ import with_statement
import sys
import Live
import LiveUtils
from _Framework.ControlSurface import ControlSurface
from ControlSurfaceComponents.LoopingEncoderElement import LoopingEncoderElement
from LiveWrappers.LiveWrapper import LiveWrapper
from LiveWrappers.LiveSong import LiveSong
from LiveNetworkEndpoint import LiveNetworkEndpoint
from Logger import Log


class ShowtimeBridge(ControlSurface):
    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        with self.component_guard():
            self.cInstance = c_instance
            self._suppress_send_midi = True
            self.endpoint = None

            Log.set_logger(self.log_message)
            Log.set_log_level(Log.LOG_WARN)
            Log.set_log_network(True)
            Log.write("-----------------------")
            Log.write("ShowtimeBridge starting")
            Log.write("Python version " + sys.version)
            Log.info(sys.version)

            # Network endpoint
            self.endpoint = LiveNetworkEndpoint()
            self.endpoint.set_song_root_accessor(LiveUtils.getSong)
            LiveWrapper.set_endpoint(self.endpoint)

            # Midi clock to trigger incoming message check
            self.clock = LoopingEncoderElement(0, 119)

            self.refresh_state()
            self._suppress_send_midi = False

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
        self.request_loop()
        ControlSurface.receive_midi(self, midi_bytes)

    def suggest_map_mode(self, cc_no, channel):
        return Live.MidiMap.MapMode.absolute

    def update_display(self):
        # Call the request handler so that messages will always be accepted
        self.request_loop()
        ControlSurface.update_display(self)

    def request_loop(self):
        self.endpoint.poll()
        if len(LiveSong.instances()) > 0:
            LiveSong.instances()[0].tick()
        LiveWrapper.process_deferred_actions()
