import sys
import Live
import ShowtimeLive.LiveUtils as LiveUtils
from _Framework.ControlSurface import ControlSurface
from _Framework.EncoderElement import *

import ShowtimeLive.showtime as showtime

import ShowtimeLive.LiveWrappers.LiveSong
from ShowtimeLive.LiveWrappers.LiveSong import LiveSong

from ShowtimeLive.LiveWrappers.LiveWrapper import LiveWrapper
from ShowtimeLive.Logger import Log

class ShowtimeBridge(ControlSurface):
    launched = False
    client = None

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self.cInstance = c_instance

        # self._suppress_send_midi = True

        # Showtime init
        Log.level = Log.LOG_DEBUG
            
        # self.refresh_state()
        # self._suppress_send_midi = False

    def disconnect(self):
        Log.write("Showtime-Live disconnecting {0}".format(id(self)))
        if hasattr(self, "client"):
            if showtime.client().connection_events():
                if hasattr(showtime.client().connection_events(), "connected_to_stage"):
                    showtime.client().connection_events().connected_to_stage.remove(self.on_connected)
                if hasattr(showtime.client().connection_events(), "disconnected_from_stage"):
                    showtime.client().connection_events().disconnected_from_stage.remove(self.on_disconnected)
            if showtime.NATIVE:
                showtime.client().destroy()
        Log.write("------------------")

    # def __del__(self):
    #     Log.write("Showtimebridge del()")
    #     self.disconnect()

    def on_connected(self, client, server, *args):
        Log.write("Showtime bridge connected to stage server {}".format(server.address))

    def on_disconnected(self, client, server, *args):
        Log.write("Showtime bridge disconnected from stage server")

    def update_display(self):
        # Call the request handler so that messages will always be accepted
        self.request_loop()
        ControlSurface.update_display(self)

    def request_loop(self):
        # Handle incoming Showtime events
        showtime.poll()
        LiveWrapper.process_deferred_actions()

    # def suggest_input_port(self):
    #     u"""Live -> Script
    #     Live can ask the script for an input port name to find a suitable one.
    #     """
    #     return 'RemoteSL'

    # def suggest_output_port(self):
    #     u"""Live -> Script
    #     Live can ask the script for an output port name to find a suitable one.
    #     """
    #     return 'RemoteSL'

    def can_lock_to_devices(self):
        u"""Live -> Script
        Live can ask the script whether it can be locked to devices
        """
        return False

    def connect_script_instances(self, instanciated_scripts):
        u"""
        Called by the Application as soon as all scripts are initialized.
        You can connect yourself to other running scripts here, as we do it
        connect the extension modules (MackieControlXTs).
        """
        Log.write("All control scripts loaded")

        # Root song object for the current set
        if not ShowtimeBridge.launched:
            Log.write("First launch detected, ignoring so Live doesn't break >:(")
            ShowtimeBridge.launched = True
            return

        Log.write("-----------------------")
        Log.write("Showtime-Live starting {0}".format(id(self)))

        Log.write(str(showtime.client().connection_events()))
        showtime.client().connection_events().connected_to_server.add(self.on_connected)
        showtime.client().connection_events().disconnected_from_server.add(self.on_disconnected)

        if showtime.NATIVE:
            showtime.client().init("LiveBridge", True)
            showtime.client().auto_join_by_name("Live")

        self.song = LiveSong("song", LiveUtils.getSong())
        self.song.refresh_hierarchy(False)
        showtime.client().get_root().add_child(self.song.component)
