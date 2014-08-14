from PyroWrappers import *


class PyroDeviceActions:
    # Outgoing
    PARAMETERS_UPDATED = "parameters_updated"


class PyroDevice(PyroWrapper):
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
        self.publisher.publish_check(PyroShared.OUTGOING_PREFIX + PyroDeviceActions.PARAMETERS_UPDATED, {
            "track": self.track.name,
            "device": self.get_reference().name})
