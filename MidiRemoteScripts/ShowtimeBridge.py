import sys
import Live
import LiveUtils
from _Framework.ControlSurface import ControlSurface
from _Framework.EncoderElement import *

from Logger import Log
import showtime
from showtime import API as ZST

from LiveWrappers.LiveSong import LiveSong


class ShowtimeBridge(ControlSurface):
    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        with self.component_guard():
            self.cInstance = c_instance
            self._suppress_send_midi = True

            # Showtime init
            Log.write("-----------------------")
            Log.write("Showtime-Live starting")

            self.client = ZST.ShowtimeClient() if showtime.NATIVE else showtime.client()
            self.client.connection_events().connected_to_server.add(self.on_connected)
            self.client.connection_events().disconnected_from_server.add(self.on_disconnected)

            if showtime.NATIVE:
                self.client.init("LiveBridge", True)
                self.client.autojoin_by_name("stage")

            # Root song object for the current set
            self.song = LiveSong("song", LiveUtils.getSong())
            self.client.get_root().add_child(self.song.component)
            self.song.refresh_hierarchy(False)

            self.refresh_state()
            self._suppress_send_midi = False

    def __del__(self):
        if hasattr(self, "client"):
            self.client.connection_events().connected_to_stage.add(self.on_connected)
            self.client.connection_events().disconnected_from_stage.add(self.on_disconnected)
            if showtime.NATIVE:
                self.client.destroy()

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
        if showtime.NATIVE:
            self.client.poll_once()
        else:
            showtime.poll()
