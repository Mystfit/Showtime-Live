from LiveWrapper import *
from LiveTrack import LiveTrack
import itertools
from ..Utils import Utils


class LiveSong(LiveWrapper):
    # Message types
    # SONG_LAYOUT = "song_layout"
    # SONG_TRACKS_UPDATED = "song_tracks_updated"
    # SONG_METERS = "song_meters"
    # SONG_LOGGING_LEVEL = "log_level"
    # SONG_NETWORK_LOGGING = "log_network"

    def create_handle_id(self):
        return "song"

    # -------------------
    # Wrapper definitions
    # -------------------
    def create_listeners(self):
        LiveWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_current_song_time_listener(self.song_time_updated)
            self.handle().add_tracks_listener(self.update_hierarchy)
            self.handle().add_return_tracks_listener(self.update_hierarchy)

    def destroy_listeners(self):
        LiveWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_current_song_time_listener(self.song_time_updated)
                self.handle().remove_tracks_listener(self.update_hierarchy)
                self.handle().remove_return_tracks_listener(self.update_hierarchy)
            except (RuntimeError, AttributeError):
                Log.warn("Couldn't remove device listener")

    # --------
    # Outgoing
    # --------
    def song_time_updated(self):
        self.tick()
        meterLevels = {}
        for track in LiveTrack.instances():
            if track:
                # Batch track meters into one message
                if track.handle():
                    if track.handle().has_midi_output:
                        Utils.truncate_float(track.handle().output_meter_level, 4)
                    else:
                        meterLevels[track.id()] = Utils.truncate_float(((track.handle().output_meter_left + track.handle().output_meter_right) * 0.5), 4)
        self.update(LiveSong.SONG_METERS, meterLevels)

    # ---------
    # Hierarchy
    # ---------
    def update_hierarchy(self):
        Log.info("%s - Track list changed" % self.id())
        tracks = list(itertools.chain(self.handle().tracks, self.handle().return_tracks))
        LiveWrapper.update_hierarchy(self, LiveTrack, tracks)

    # ---------
    # Utilities
    # ---------
    def tick(self):
        for track in LiveTrack.instances():
            track.tick()