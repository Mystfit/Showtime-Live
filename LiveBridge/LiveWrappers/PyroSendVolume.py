from PyroWrappers import *


class PyroSendVolumeActions:
    # Outgoing
    SEND_UPDATED = "send_updated"


class PyroSendVolume(PyroWrapper):
    def __init__(self, trackindex, sendindex, publisher):
        PyroWrapper.__init__(self, publisher=publisher)
        self.trackindex = trackindex
        self.sendindex = sendindex
        self.ref_wrapper = self.get_send
        self.get_reference().add_value_listener(self.send_updated)

    def get_send(self):
        return getTrack(self.trackindex).mixer_device.sends[self.sendindex]

    def send_updated(self):
        self.publisher.publish_check(PyroShared.OUTGOING_PREFIX + PyroSendVolumeActions.SEND_UPDATED, {
            "trackindex": self.trackindex,
            "sendindex": self.sendindex,
            "value": self.get_reference().value})
