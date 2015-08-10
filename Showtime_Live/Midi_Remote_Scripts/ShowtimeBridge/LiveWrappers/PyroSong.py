from PyroWrapper import *
from PyroTrack import PyroTrack


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
            self.handle().add_tracks_listener(self.song_tracks_updated)
            self.handle().add_return_tracks_listener(self.song_tracks_updated)


    def destroy_listeners(self):
        PyroWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_current_song_time_listener(self.song_time_updated)
                self.handle().remove_tracks_listener(self.song_tracks_updated)
                self.handle().remove_return_tracks_listener(self.song_tracks_updated)
            except RuntimeError:
                Log.write("Couldn't remove device listener")


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

    def song_tracks_updated(self, *args):
        self.update_hierarchy()

    # --------
    # Incoming
    # --------
    @staticmethod
    def build_song_layout(args):
        Log.write("Inside JSON track formatter")

        trackgroup = None

        if("category" in args):
            Log.write("Category is " + str(args["category"]))

            if int(args["category"]) == 0:
                trackgroup = handle().tracks
            elif int(args["category"]) == 1:
                trackgroup = handle().return_tracks

            if(trackgroup):
                Log.write("Trackgroup is " + str(trackgroup))
                tracks = self.tracks_to_object(trackgroup)
                Log.write(tracks)
            else:
                tracks = {"error" : "Category argument out of range"}
        else:
            tracks = {"error" : "Category argument missing"}

        PyroSong.findById(args["id"]).update(PyroSong.SONG_LAYOUT, tracks)

    # ---------
    # Utilities
    # ---------

    # ---------
    # Hierarchy
    def update_hierarchy(self):
        Log.write("Track list changed")
        PyroWrapper.update_hierarchy(self, PyroTrack, self.handle().tracks)
        # PyroWrapper.update_hierarchy(self, PyroTrack, self.handle().return_tracks)

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
                return "!!! Error parsing track"

            for deviceindex, device in enumerate(track.devices):

                for parameterindex, parameter in enumerate(device.parameters):
                    self.log_message("Parsing param " + str(parameter.name))

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
                        return "!!! Error parsing parameter"
                    trackObj["parameters"].append(paramObj)
            tracks["tracklist"].append(trackObj)
        return tracks
