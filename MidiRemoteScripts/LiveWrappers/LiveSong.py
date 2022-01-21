import itertools

from ShowtimeLive.LiveWrappers.LiveWrapper import LiveWrapper
from ShowtimeLive.LiveWrappers.LiveTrack import LiveTrack

from ShowtimeLive.showtimeAPI import API as ZST
from ShowtimeLive.Utils import Utils
from ShowtimeLive.Logger import Log

import ShowtimeLive.showtimeAPI as showtime

class LiveSong(LiveWrapper):
    def __init__(self, name, handle):
        LiveWrapper.__init__(self, name, handle, 0)
        self.returns = ZST.ZstComponent("returns")
        self.tracks = ZST.ZstComponent("tracks")
        showtime.client().register_entity(self.returns)
        showtime.client().register_entity(self.tracks)
        self.master = LiveTrack("master", self.handle().master_track, 0)

    def on_registered(self, entity):
        Log.write("Song registered")
        LiveWrapper.on_registered(self, entity)
        self.component.add_child(self.returns)
        self.component.add_child(self.tracks)
        self.component.add_child(self.master.component)


    @staticmethod
    def build_name(handle, handle_index):
        return "song"

    # -------------------
    # Wrapper definitions
    # -------------------
    def create_listeners(self):
        LiveWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_current_song_time_listener(self.song_time_updated)
            self.handle().add_tracks_listener(self.refresh_tracks)
            self.handle().add_return_tracks_listener(self.refresh_returns)
        else:
            Log.write("No song handle")

    def destroy_listeners(self):
        LiveWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_current_song_time_listener(self.song_time_updated)
                self.handle().remove_tracks_listener(self.refresh_tracks)
                self.handle().remove_return_tracks_listener(self.refresh_returns)
            except (RuntimeError, AttributeError):
                Log.warn("Couldn't remove device listener")

    # --------
    # Outgoing
    # --------
    def song_time_updated(self):
        self.tick()
        meterLevels = {}
        for track_handle in self.handle().tracks:
            track = LiveWrapper.find_wrapper_from_live_ptr(track_handle._live_ptr)
            if track:
                if track.handle().has_midi_output:
                    Utils.truncate_float(track.handle().output_meter_level, 4)
                else:
                    meterLevels[track.URI().path()] = Utils.truncate_float(((track.handle().output_meter_left + track.handle().output_meter_right) * 0.5), 4)

    # ---------
    # Hierarchy
    # ---------

    def refresh_tracks(self, postactivate=True):
        Log.info("{0} - Track list changed".format(self.component.URI().last().path()))
        LiveWrapper.update_hierarchy(self.tracks, LiveTrack, self.handle().tracks, postactivate)

    def refresh_returns(self, postactivate=True):
        Log.info("{0} - Returns list changed".format(self.component.URI().last().path()))
        LiveWrapper.update_hierarchy(self.returns, LiveTrack, self.handle().return_tracks, postactivate)

    def refresh_hierarchy(self, postactivate):
        self.refresh_tracks(postactivate)
        self.refresh_returns(postactivate)


    # ---------
    # Utilities
    # ---------
    def tick(self):
        for track_handle in self.handle().tracks:
            track = LiveWrapper.find_wrapper_from_live_ptr(track_handle._live_ptr)
            if track:
                track.tick()
