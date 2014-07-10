from PyroWrappers import *
from PyroTrack import PyroTrack
from PyroDevice import PyroDevice
from PyroDeviceParameter import PyroDeviceParameter
from PyroSend import PyroSend
from PyroSendVolume import PyroSendVolume


class PyroSongActions:
    # Incoming
    FIRE_CLIP = "fire_clip"
    SET_VALUE = "set_value"
    GET_SONG_LAYOUT = "get_song_layout"
    STOP_TRACK = "stop_track"
    SET_SEND = "set_send"


class PyroSong(PyroWrapper):
    def __init__(self, publisher, logger):
        PyroWrapper.__init__(self, publisher=publisher)
        self.log_message = logger
        self.ignoreList = []
        self.ref_wrapper = self.get_song
        self.parameters = {}
        self.tracks = []
        self.returns = []
        self.valueChangedMessages = {}

        self.incomingActions[PyroSongActions.SET_VALUE] = self.set_value
        self.incomingActions[PyroSongActions.GET_SONG_LAYOUT] = self.get_song_layout
        self.incomingActions[PyroSongActions.FIRE_CLIP] = self.fire_clip
        self.incomingActions[PyroSongActions.STOP_TRACK] = self.stop_track
        self.incomingActions[PyroSongActions.SET_SEND] = self.set_send

    def get_song(self):
        return getSong()

    def build_wrappers(self):
        for trackindex in range(len(getTracks())):
            trackWrapper = PyroTrack(trackindex, self.publisher)
            self.tracks.append(trackWrapper)

            for deviceindex in range(len(getTrack(trackindex).devices)):
                deviceWrapper = PyroDevice(trackindex, deviceindex, self.publisher)
                trackWrapper.devices.append(deviceWrapper)

                for parameterindex in range(len(getTrack(trackindex).devices[deviceindex].parameters)):
                    parameterWrapper = PyroDeviceParameter(trackindex, deviceindex, parameterindex, self.publisher)
                    self.parameters[(trackindex, deviceindex, parameterindex, 0)] = parameterWrapper

            sendlist = trackWrapper.get_reference().mixer_device.sends
            for send in range(len(sendlist)):
                sendParamWrapper = PyroSendVolume(trackindex, send, self.publisher)
                trackWrapper.sends.append(sendParamWrapper)

        for sendindex in range(len(getSong().return_tracks)):
            sendWrapper = PyroSend(sendindex, self.publisher)
            self.returns.append(sendWrapper)

            for deviceindex in range(len(sendWrapper.get_reference().devices)):
                deviceWrapper = PyroDevice(sendindex, deviceindex, self.publisher, 1)
                sendWrapper.devices.append(deviceWrapper)

                for parameterindex in range(len(sendWrapper.get_reference().devices[deviceindex].parameters)):
                    parameterWrapper = PyroDeviceParameter(sendindex, deviceindex, parameterindex, self.publisher, 1)
                    self.parameters[(sendindex, deviceindex, parameterindex, 1)] = parameterWrapper

    def process_value_changed_messages(self):
        if self.valueChangedMessages:
            for parametertuple, value in self.valueChangedMessages.iteritems():
                try:
                    if parametertuple in self.parameters:
                        self.parameters[parametertuple].get_reference().value = value
                except RuntimeError, e:
                    self.log_message(e)
            self.valueChangedMessages = {}

    # Incoming
    # --------
    def set_value(self, args):
        key = (
            int(args["trackindex"]),
            int(args["deviceindex"]),
            int(args["parameterindex"]),
            int(args["category"]))

        # Rather than setting the parameter value immediately,
        # we combine similar value messages so only the most up to date
        # message gets applied when the clock triggers our update
        if not self.valueChangedMessages:
            self.valueChangedMessages = {}
        self.valueChangedMessages[key] = float(args["value"])

    def fire_clip(self, args):
        self.log_message(launchClip)
        launchClip(int(args["trackindex"]), int(args["clipindex"]))
        self.log_message("Clip not found! " + str(args["trackindex"]) + ", " + str(args["clipindex"]))

    def stop_track(self, args):
        self.log_message("Stopping track " + str(args["trackindex"]))
        stopTrack(int(args["trackindex"]))
        self.log_message("Stopped track")

    def set_send(self, args):
        self.log_message("Setting send value " + str(args["trackindex"]))
        trackSend(int(args["trackindex"]), int(args["sendindex"]), float(args["value"]))

    # Outgoing
    # --------
    def get_song_layout(self, args=None):
        self.publisher.publish_check(
            PyroShared.OUTGOING_PREFIX + PyroSongActions.GET_SONG_LAYOUT, self.dump_song_xml())

    def clips_to_json(self):
        return None

    def tracks_to_json(self):
        tracks = []
        for track in len(getTracks()):
            t = getTracks()[track]
            mixer = t.mixer_device

            sends = []
            for send in mixer.sends:
                sends.append({
                    "name": send.name,
                    "value": send.value,
                    "min": send.min,
                    "max": send.max})

            trackobj = {
                "trackindex": track,
                "name": t.name,
                "armed": (True if r.can_be_armed else False),
                "volume": mixer.volume,
                "pan": mixer.panning,
                "solo": t.solo,
                "mute": t.mute,
                "sends": sends}
            tracks.append(trackobj)

    def parameters_to_json(self, trackgroup):
        parameters = []
        for track in len(trackgroup):
            for device in len(track.devices):
                for parameter in len(device.parameters):
                    param = track.devices[device].parameters[parameter]
                    paramObj = {
                        "trackindex": track,
                        "deviceindex": device,
                        "parameterindex": parameter,
                        "name": param.name,
                        "min": param.min,
                        "max": param.max,
                        "value": param.value}
                    parameters.append(paramObj)
        return parameters

    def dump_song_xml(self):
        xmlString = "<?xml version='1.0' encoding='UTF-8'?>\n"
        xmlString += "<song tempo = '" + \
            str(getSong().tempo) + "'>\n"
        trackIndex = 0

        # iterate through the tracks
        for myTrack in getTracks():

            myTrackMixer = myTrack.mixer_device

            try:
                myTrackMixer = myTrack.mixer_device

                # Ignore specific devices, OSC senders and stuff
                ignoreTrack = False
                for i in range(len(self.ignoreList)):
                    if str(self.ignoreList[i]) in str(myTrack.name):
                        ignoreTrack = True
                if(ignoreTrack):
                    continue

                armed = False
                if(myTrack.can_be_armed):
                    armed = myTrack.arm

                xmlString += "\t<track index='" + str(trackIndex) + "' name='" + str(myTrack.name) + "' volume='" + str(myTrackMixer.volume) + "' pan='" + str( \
                    myTrackMixer.panning) + "' output_meter_level='" + str(myTrack.output_meter_level) + "' mute='" + str(myTrack.mute) + "' solo='" + \
                    str(myTrack.solo) + "' midi='" + str(myTrack.has_midi_input) + "' armed='" + str(armed) + "' color='" + str(myTrack.color) + "'>\n"

                clipIndex = 0

                # iterate through clips of a track
                for myClipSlot in myTrack.clip_slots:
                    if (myClipSlot.has_clip):
                        try:
                            myClip = myClipSlot.clip
                            xmlString += "\t\t<clip index='" + str(clipIndex) + "' name='" + myClip.name + "' color='" + str(myClip.color) + "' mute='" + \
                                str(myClip.muted) + "' looping='" + str(myClip.looping) + "' playing='" + \
                                str(myClip.is_playing) + "' triggered='" + \
                                str(myClip.is_triggered) + \
                                "' />\n"
                        except:
                            return ("!! error parsingclip !!")
                    clipIndex += 1

                sendIndex = 0
                # get sends
                for mySends in myTrackMixer.sends:
                    xmlString += "\t\t<sends index='" + str(sendIndex) + "' name='" + \
                        str(mySends.name) + "' value='" + str(
                            mySends.value) + "' min='" + str(mySends.min) + "' max='" + str(mySends.max) + "' />\n"
                    sendIndex += 1

                # iterate through the device chain of a track
                # get the devices and the associated parameters
                deviceIndex = 0
                for myDevice in myTrack.devices:
                    try:
                        # Ignore specific devices, OSC senders and stuff
                        ignoreDevice = False
                        for i in range(len(self.ignoreList)):
                            if(myDevice.name.find(self.ignoreList[i]) > 0):
                                ignoreDevice = True
                        if(ignoreDevice):
                            continue
                        xmlString += "\t\t<device index='"+ str(deviceIndex) + "' name='" + \
                            str(myDevice.name) + "'>\n"
                        deviceIndex += 1
                    except:
                        return "!! error parsing Device !!"

                    parameterIndex = 0
                    for myParameter in myDevice.parameters:
                        try:
                            ignoreDeviceParam = False
                            for i in range(len(self.ignoreList)):
                                if str(self.ignoreList[i]) in str(myParameter.name):
                                    ignoreDeviceParam = True
                            if(ignoreDeviceParam):
                                continue
                            xmlString += "\t\t\t<parameter index='"+ str(parameterIndex) + "' name='" + str(myParameter.name) + "' value='" + str(
                                myParameter.value) + "' min='" + str(myParameter.min) + "' max='" + str(myParameter.max) + "'/>\n"
                            parameterIndex += 1;
                        except:
                            return "!! error parsing Parameter!!"

                    xmlString += "\t\t</device>\n"

                xmlString += "\t</track>\n"
                trackIndex += 1

            except:
                return "!! error parsing track !!"

        returnTrackIndex = 0
        # represent the Return Track
        for myReturnTrack in getSong().return_tracks:
            try:
                myReturnTrackMixer = myReturnTrack.mixer_device
                xmlString += "\t<trackReturn returnTrackIndex='" + str(returnTrackIndex) + "' name='" + str(myReturnTrack.name) + "' volume='" + str(myReturnTrackMixer.volume) + "' pan='" + str(

                    myReturnTrackMixer.panning) + "' output_meter_level='" + str(myReturnTrack.output_meter_level) + "' mute='" + str(myReturnTrack.mute) + "' solo='" + str(myReturnTrack.solo) + "' color='" + str(myReturnTrack.color) + "'>\n"

                # iterate through the device chain of a track
                # get the devices and the associated parameters
                deviceIndex = 0
                for myReturnDevice in myReturnTrack.devices:
                    try:
                        # Ignore specific devices, OSC senders and stuff
                        ignoreDevice = False
                        for i in range(len(self.ignoreList)):
                            if(myReturnDevice.name.find(self.ignoreList[i]) > 0):
                                ignoreDevice = True
                        if(ignoreDevice):
                            continue

                        xmlString += "\t\t<device index='" + str(deviceIndex) + "' name='" + \
                            str(myReturnDevice.name) + "'>\n"
                    except:
                        return "!! error parsing return Device !!"

                    parameterIndex = 0
                    for myReturnParameter in myReturnDevice.parameters:
                        try:
                            xmlString += "\t\t\t<parameter index='" + str(parameterIndex) + "' name='" + str(myReturnParameter.name) + "' value='" + str(
                                myReturnParameter.value) + "' min='" + str(myReturnParameter.min) + "' max='" + str(myReturnParameter.max) + "'/>\n"
                        except:
                            return "!! error parsing return Parameter!!"
                        parameterIndex += 1
                    xmlString += "\t\t</device>\n"
                    deviceIndex += 1

                xmlString += "\t</trackReturn>\n"
                returnTrackIndex += 1
            except:
                return "!! error parsing return !!"

        xmlString += "</song>\n"

        return xmlString
