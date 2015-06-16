from PyroWrapper import *
from PyroTrack import PyroTrack
from PyroDevice import PyroDevice
from PyroDeviceParameter import PyroDeviceParameter
from PyroSend import PyroSend

class PyroSong(PyroWrapper):
    # Message types
    SONG_LAYOUT = "song_layout"
    SONG_METERS = "song_meters"    

    def __init__(self, handle, parent=None, logger=None):
        PyroWrapper.__init__(self, handle, parent)
        self.log_message = logger
        self.handle().add_current_song_time_listener(self.song_time_updated)

    @classmethod
    def register_methods(cls):
        PyroSong.add_outgoing_method(PyroSong.SONG_METERS)
        PyroSong.add_incoming_method(PyroSong.SONG_LAYOUT, None, PyroSong.build_song_layout, True)

    def build_wrappers(self):
        # Tracks
        for trackindex, track in enumerate(self.handle().tracks):
            trackWrapper = PyroTrack(trackindex, track, self)

            # Devices
            for deviceindex, device in enumerate(track.devices):
                deviceWrapper = PyroDevice(deviceindex, device, trackWrapper)

                # Device parameters
                for parameterindex, param in enumerate(device.parameters):
                    parameterWrapper = PyroDeviceParameter(parameterindex, param, deviceWrapper)

            # # Sends
            # for sendindex, send in enumerate(trackWrapper.handle().mixer_device.sends):
            #     sendParamWrapper = PyroSendVolume(sendindex, send, trackWrapper)

        # Return tracks
        # for returntrackindex, returntrack in enumerate(self.handle().return_tracks):
        #     returnTrackWrapper = PyroReturn(returntrackindex, returntrack, self)

        #     # Return devices
        #     for deviceindex, device in enumerate(returntrack.devices):
        #         deviceWrapper = PyroDevice(deviceindex, device, returnTrackWrapper)

        #         # Return parameters
        #         for parameterindex, parameter in enumerate(device.parameters):
        #             parameterWrapper = PyroDeviceParameter(parameterindex, parameter, deviceWrapper)

    def song_time_updated(self):
        meterLevels = []
        for track in PyroTrack.instances():
            if not track.handle().has_midi_output:
                meterLevels.append((track.handle().output_meter_left + track.handle().output_meter_right) * 0.5)
            else:
                meterLevels.append(track.handle().output_meter_level)

        self.update(PyroSong.SONG_METERS, meterLevels)

    # Incoming
    # --------

    # Outgoing
    # --------

    @staticmethod
    def build_song_layout(args):
        self.log_message("Inside JSON track formatter")

        trackgroup = None

        if("category" in args):
            self.log_message("Category is " + str(args["category"]))

            if int(args["category"]) == 0:
                trackgroup = getTracks()
            elif int(args["category"]) == 1:
                trackgroup = getSong().return_tracks

            if(trackgroup):
                self.log_message("Trackgroup is " + str(trackgroup))
                tracks = self.tracks_to_object(trackgroup)
                self.log_message(tracks)
            else:
                tracks = {"error" : "Category argument out of range"}
        else:
            tracks = {"error" : "Category argument missing"}

        PyroSong.findById(args["id"]).update(PyroSong.SONG_LAYOUT, tracks)

    def clips_to_json(self):
        return None

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
