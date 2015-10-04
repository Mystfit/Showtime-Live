from PyroWrapper import *
from PyroTrack import PyroTrack
import itertools

class PyroSong(PyroWrapper):
    # Message types
    SONG_LAYOUT = "song_layout"
    SONG_TRACKS_UPDATED = "song_tracks_updated"
    SONG_METERS = "song_meters"

    # -------------------
    # Wrapper definitions
    # -------------------
    def create_listeners(self):
        PyroWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_current_song_time_listener(self.song_time_updated)
            self.handle().add_tracks_listener(self.update_hierarchy)
            self.handle().add_return_tracks_listener(self.update_hierarchy)


    def destroy_listeners(self):
        PyroWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_current_song_time_listener(self.song_time_updated)
                self.handle().remove_tracks_listener(self.update_hierarchy)
                self.handle().remove_return_tracks_listener(self.update_hierarchy)
            except RuntimeError:
                Log.warn("Couldn't remove device listener")


    @classmethod
    def register_methods(cls):
        PyroSong.add_outgoing_method(PyroSong.SONG_METERS)
        PyroSong.add_outgoing_method(PyroSong.SONG_TRACKS_UPDATED)
        PyroSong.add_incoming_method(PyroSong.SONG_LAYOUT, None, PyroSong.build_song_layout, True)

    # --------
    # Outgoing
    # --------
    def song_time_updated(self):
        meterLevels = []
        for track in PyroTrack.instances():
            if not track.handle().has_midi_output:
                meterLevels.append((track.handle().output_meter_left + track.handle().output_meter_right) * 0.5)
            else:
                meterLevels.append(track.handle().output_meter_level)
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
            song = PyroSong.instances()[0]
        except Exception, e:
            Log.warn("Couldn't get song wrapper. " + str(e))

        wrappers = []
        try:
            for cls in PyroWrapper.__subclasses__():
                Log.info("Converting %s instances to objects" % cls.__name__)
                for instance in cls.instances():
                    wrappers.append(instance.toObject())
                    Log.info(instance.toObject())
        except:
            Log.error("Couldn't build song list")
        
        song.respond(PyroSong.SONG_LAYOUT, wrappers)


    # ---------
    # Hierarchy

    def update_hierarchy(self):
        Log.info("Track list changed")
        tracks = list(itertools.chain(self.handle().tracks, self.handle().return_tracks))
        PyroWrapper.update_hierarchy(self, PyroTrack, tracks)

    def tracks_to_object(self, trackgroup):
        tracks = {"tracklist":[]}
        for trackindex, track in enumerate(trackgroup):
            mixer = track.mixer_device
            sends = []

            try:
                trackObj = {
                    "trackindex": trackindex,
                    "name": track.name,
                    "armed": (track.arm if track.can_be_armed else False),
                    "volume": ({
                            "name": mixer.volume.name,
                            "min": mixer.volume.min,
                            "max": mixer.volume.max,
                            "value": mixer.volume.value
                        } if not track.has_midi_output else None),
                    "pan": ({
                            "name": mixer.panning.name,
                            "min": mixer.panning.min,
                            "max": mixer.panning.max,
                            "value": mixer.panning.value
                        } if not track.has_midi_output else None),
                    "solo": track.solo,
                    "color": track.color,
                    "mute": track.mute,
                    "sends": sends,
                    "midi": track.has_midi_input,
                    "parameters": []}
            except:
                Log.error("Error parsing track")
                return

            for deviceindex, device in enumerate(track.devices):
                for parameterindex, parameter in enumerate(device.parameters):
                    try:
                        paramObj = {
                            "trackindex": trackindex,
                            "deviceindex": deviceindex,
                            "parameterindex": parameterindex,
                            "min": parameter.min,
                            "max": parameter.max,
                            "value": parameter.value,
                            "name": parameter.name
                        }
                    except:
                        Log.error("Error parsing parameter")
                        return

                    trackObj["parameters"].append(paramObj)
            tracks["tracklist"].append(trackObj)
        return tracks
