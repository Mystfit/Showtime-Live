from __future__ import with_statement

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "ext_libs"))

import encodings

# Import Live libraries
import Live
from _Framework.ControlSurface import ControlSurface
from _Framework.EncoderElement import EncoderElement

# Import custom live objects
from LiveUtils import *
from ControlSurfaceComponents import *
from ControlSurfaceComponents.PyroEncoderElement import PyroEncoderElement

from LiveWrappers.LiveWrapper import LiveWrapper
from LiveWrappers.LiveDevice import LiveDevice
from LiveWrappers.LiveDeviceParameter import LiveDeviceParameter
from LiveWrappers.LiveSend import LiveSend
from LiveWrappers.LiveSong import LiveSong
from LiveWrappers.LiveTrack import LiveTrack

from LiveUDPEndpoint import LiveUDPEndpoint
from Logger import Log


class ShowtimeBridge(ControlSurface):
    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        with self.component_guard():
            self.cInstance = c_instance
            self._suppress_send_midi = True

            Log.set_logger(self.log_message)
            Log.set_log_level(Log.LOG_WARN)
            Log.write("-----------------------")
            Log.write("ShowtimeBridge starting")
            Log.info(sys.version)

            self.initServer()

            # Register methods to the showtimebridge server
            wrapperClasses = LiveWrapper.__subclasses__()
            wrapperClasses.append(LiveWrapper)
            for cls in wrapperClasses:  
                cls.clear_instances()
                cls.register_methods()
                for action in cls.incoming_methods().values():
                    Log.info("Adding %s to incoming callbacks" % action.methodName)
                    self.endpoint.add_incoming_action(action.methodName, cls, action.callback)
                    self.endpoint.register_to_showtime(action.methodName, action.methodAccess, action.methodArgs)

                for action in cls.outgoing_methods().values():
                    Log.info("Adding %s to outgoing methods" % action.methodName)
                    self.endpoint.register_to_showtime(action.methodName, action.methodAccess)

            # Midi clock to trigger incoming message check
            self.clock = PyroEncoderElement(0, 119)

            # Create the root wrapper
            LiveSong.add_instance(LiveSong(getSong()))

            self.refresh_state()
            self._suppress_send_midi = False

    def initServer(self):
        self.endpoint = LiveUDPEndpoint(6002, 6001, False)

        # Set the global publisher for all wrappers
        LiveWrapper.set_publisher(self.endpoint)

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
        #Call the pyro request handler so that messages will always be accepted
        self.requestLoop()
        ControlSurface.update_display(self)

    def requestLoop(self):
        self.endpoint.handle_requests()
        LiveWrapper.process_deferred_actions()
