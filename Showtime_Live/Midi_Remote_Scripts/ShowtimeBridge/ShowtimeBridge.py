from __future__ import with_statement

# Append Pyro and missing standard python scripts to the path
import sys
#sys.path.append("/System/Library/Frameworks/Python.framework/Versions/2.5/lib/python2.5")
#sys.path.append("/System/Library/Frameworks/Python.framework/Versions/2.5/lib/python2.5/lib-dynload")

import os
sys.path.append(os.path.join(os.path.dirname(__file__), "ext_libs"))

import encodings

# Import pyro
import Pyro.naming
import Pyro.errors
import Pyro.core
Pyro.config.PYRO_STORAGE = "/tmp"

# Import Live libraries
import Live
from _Framework.ControlSurface import ControlSurface
from _Framework.EncoderElement import EncoderElement

# Import custom live objects
from LiveUtils import *
from ControlSurfaceComponents import *
from ControlSurfaceComponents.PyroEncoderElement import PyroEncoderElement
from LiveSubscriber import LiveSubscriber
from LiveWrappers.PyroWrapper import PyroWrapper
from LiveWrappers.PyroSong import PyroSong
from LivePublisher import LivePublisher


class ShowtimeBridge(ControlSurface):

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        with self.component_guard():
            self.cInstance = c_instance
            self._suppress_send_midi = True

            self.log_message(self, "--------------------")
            self.log_message(self, "ShowtimeBridge START")

            # Wrappers for Ableton objects
            self.song = None
            self.tracks = []
            self.sends = []
            self.clock = None

            self.initPyroServer()
            self.songWrapper = PyroSong(getSong(), None, self.log_message)

            # Register methods to the showtimebridge server
            for cls in PyroWrapper.__subclasses__():
                cls.register_methods()
                for action in cls.incoming_methods().values():
                    self.log_message("Adding " + str(action) + " to incoming callbacks")
                    self.subscriber.add_incoming_action(action.methodName, action.callback)
                    self.publisher.register_to_showtime(action.methodName, action.methodAccess, action.methodArgs)

                for action in cls.outgoing_methods().values():
                    self.log_message("Adding " + str(action) + " to outgoing methods")
                    self.publisher.register_to_showtime(action.methodName, action.methodAccess)

            # Midi clock to trigger incoming message check
            self.clock = PyroEncoderElement(0, 119)
            self.songWrapper.build_wrappers()

            self.refresh_state()
            self._suppress_send_midi = False


    def initPyroServer(self):
        Pyro.config.PYRO_ES_BLOCKQUEUE = False

        # Event listener
        Pyro.core.initClient()

        # Create publisher and subscriber links to event server
        self.publisher = LivePublisher(self.log_message)
        self.subscriber = LiveSubscriber(self.publisher, self.log_message)

        # Set the global publisher for all wrappers
        PyroWrapper.set_publisher(self.publisher)

    def disconnect(self):
        self._suppress_send_midi = True
        self._suppress_send_midi = False
        ControlSurface.disconnect(self)

    def refresh_state(self):
        ControlSurface.refresh_state(self)
        self.request_rebuild_midi_map()

    def build_midi_map(self, midi_map_handle):
        self.log_message("Building midi map...")
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
        self.subscriber.handle_requests()
