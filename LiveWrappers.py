try:
    from LiveUtils import *
except ImportError:
    print "Couldn't import LiveUtils!"

import Pyro.errors

INCOMING_PREFIX = "I_"
OUTGOING_PREFIX = "O_"


class PyroWrapper():
    def __init__(self, publisher):
        self.publisher = publisher
        self.ref_wrapper = None

    def get_reference(self):
        return self.ref_wrapper()


class PyroSong(PyroWrapper):

    # Out
    GET_SONG_LAYOUT = "get_song_layout"

    def __init__(self, publisher):
        PyroWrapper.__init__(self, publisher=publisher)
        self.ignoreList = []
        self.ref_wrapper = getSong

    def get_song_layout(self, args=None):
        self.publisher.publish_check(
            OUTGOING_PREFIX + PyroSong.GET_SONG_LAYOUT, self.dump_song_xml())

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


class PyroTrack(PyroWrapper):
    # Out
    FIRED_SLOT_INDEX = "fired_slot_index"
    PLAYING_SLOT_INDEX = "playing_slot_index"

    # In
    FIRE_CLIP = "fire_clip"
    STOP_TRACK = "stop_track"

    def __init__(self, trackindex, publisher):
        PyroWrapper.__init__(self, publisher=publisher)
        self.trackindex = trackindex
        self.devices = []
        self.sends = []
        self.ref_wrapper = self.get_track

        # Listeners
        self.get_reference().add_fired_slot_index_listener(self.fired_slot_index)
        self.get_reference().add_playing_slot_index_listener(self.playing_slot_index)

    def get_track(self):
        return getSong().tracks[self.trackindex]

    def fired_slot_index(self):
        self.publisher.publish_check(OUTGOING_PREFIX + PyroTrack.FIRED_SLOT_INDEX, {
            "trackindex": self.trackindex,
            "slotindex": self.get_reference().fired_slot_index})

    def playing_slot_index(self):
        self.publisher.publish_check(OUTGOING_PREFIX + PyroTrack.PLAYING_SLOT_INDEX, {
            "trackindex": self.trackindex,
            "slotindex": self.get_reference().playing_slot_index})


class PyroSend(PyroWrapper):
    # Out
    # In

    def __init__(self, sendindex, publisher):
        PyroWrapper.__init__(self, publisher=publisher)
        self.sendindex = sendindex
        self.publisher = publisher
        self.devices = []
        self.ref_wrapper = self.get_send

    def get_send(self):
        return getSong().return_tracks[self.sendindex]


class PyroDevice(PyroWrapper):
    # Out
    PARAMETERS_UPDATED = "parameters_updated"

    def __init__(self, trackindex, deviceindex, publisher, isSendDevice=False):
        PyroWrapper.__init__(self, publisher=publisher)
        self.trackindex = trackindex
        self.deviceindex = deviceindex
        self.parameters = []
        self.isSendDevice = isSendDevice
        self.ref_wrapper = self.get_device
        self.get_reference().add_parameters_listener(self.parameters_updated)

    def get_device(self):
        if self.isSendDevice:
            return getSong().return_tracks[self.trackindex].devices[self.deviceindex]
        return getTrack(self.trackindex).devices[self.deviceindex]

    def parameters_updated(self):
        self.publisher.publish_check(OUTGOING_PREFIX + PyroDevice.PARAMETERS_UPDATED, {
            "track": self.track.name,
            "device": self.get_reference().name})


class PyroDeviceParameter(PyroWrapper):
    # Out
    VALUE_UPDATED = "value_updated"

    #In
    SET_VALUE = "set_value"

    def __init__(self, trackindex, deviceindex, parameterindex, publisher, isSendDeviceParameter=0):
        PyroWrapper.__init__(self, publisher=publisher)
        self.trackindex = trackindex
        self.deviceindex = deviceindex
        self.parameterindex = parameterindex
        self.isSendDeviceParameter = isSendDeviceParameter
        self.ref_wrapper = self.get_parameter
        self.get_reference().add_value_listener(self.value_updated)

    def get_parameter(self):
        if self.isSendDeviceParameter:
            return getSong().return_tracks[self.trackindex].devices[self.deviceindex].parameters[self.parameterindex]
        return getTrack(self.trackindex).devices[self.deviceindex].parameters[self.parameterindex]

    def value_updated(self):
        self.publisher.publish_check(OUTGOING_PREFIX + PyroDeviceParameter.VALUE_UPDATED, {
            "trackindex": self.trackindex,
            "deviceindex": self.deviceindex,
            "parameterindex": self.parameterindex,
            "value": self.get_reference().value,
            "category": self.isSendDeviceParameter})


class PyroSendVolume(PyroWrapper):
    #Out
    SEND_UPDATED = "send_updated"

    #In
    SET_SEND = "set_send"

    def __init__(self, trackindex, sendindex, publisher):
        PyroWrapper.__init__(self, publisher=publisher)
        self.trackindex = trackindex
        self.sendindex = sendindex
        self.ref_wrapper = self.get_send
        self.get_reference().add_value_listener(self.send_updated)

    def get_send(self):
        return getTrack(self.trackindex).mixer_device.sends[self.sendindex]

    def send_updated(self):
        self.publisher.publish_check(OUTGOING_PREFIX + PyroSendVolume.SEND_UPDATED, {
            "trackindex": self.trackindex,
            "sendindex": self.sendindex,
            "value": self.get_reference().value})
