from LiveWrapper import *
from LiveTrack import LiveTrack
import itertools
from ..Utils import Utils

class LiveSong(LiveWrapper):
    # Message types
    SONG_LAYOUT = "song_layout"
    SONG_TRACKS_UPDATED = "song_tracks_updated"
    SONG_METERS = "song_meters"

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
            except RuntimeError:
                Log.warn("Couldn't remove device listener")


    @classmethod
    def register_methods(cls):
        LiveSong.add_outgoing_method(LiveSong.SONG_METERS)
        LiveSong.add_outgoing_method(LiveSong.SONG_TRACKS_UPDATED)
        LiveSong.add_incoming_method(LiveSong.SONG_LAYOUT, None, LiveSong.build_song_layout, True)

    # --------
    # Outgoing
    # --------
    def song_time_updated(self):
        meterLevels = {}
        for track in PyroTrack.instances():
            if track:
                if track.handle():
                    if track.handle().has_midi_output:
                        Utils.truncate_float(track.handle().output_meter_level, 4)
                    else:
                        meterLevels[track.id()] = Utils.truncate_float(((track.handle().output_meter_left + track.handle().output_meter_right) * 0.5), 4)
        self.update(PyroSong.SONG_METERS, meterLevels)

    # --------
    # Incoming
    # --------
    @staticmethod
    def build_song_layout(args):
        Log.info("Returning song layout")
        song = None
        try:
            # Use the first song available.
            song = LiveSong.instances()[0]
        except Exception, e:
            Log.warn("Couldn't get song wrapper. " + str(e))

        wrappers = []
        for cls in LiveWrapper.__subclasses__():
            Log.info("Converting %s instances to objects" % cls.__name__)
            for instance in cls.instances():
                wrappers.append(instance.to_object())

        song.respond(LiveSong.SONG_LAYOUT, wrappers)

    # ---------
    # Hierarchy
    def update_hierarchy(self):
        Log.info("- Track list changed")
        tracks = list(itertools.chain(self.handle().tracks, self.handle().return_tracks))
        LiveWrapper.update_hierarchy(self, LiveTrack, tracks)
