from PyroWrappers import *


class PyroDeviceParameterActions:
    # Outgoing
    VALUE_UPDATED = "value_updated"


class PyroDeviceParameter(PyroWrapper):
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
        self.publisher.publish_check(PyroShared.OUTGOING_PREFIX + PyroDeviceParameterActions.VALUE_UPDATED, {
            "trackindex": self.trackindex,
            "deviceindex": self.deviceindex,
            "parameterindex": self.parameterindex,
            "value": self.get_reference().value,
            "category": self.isSendDeviceParameter})
