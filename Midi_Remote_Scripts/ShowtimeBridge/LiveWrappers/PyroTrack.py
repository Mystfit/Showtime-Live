from PyroWrappers import *


class PyroTrackActions:
    # Outgoing
    FIRED_SLOT_INDEX = "fired_slot_index"
    PLAYING_SLOT_INDEX = "playing_slot_index"


class PyroTrack(PyroWrapper):
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

    # Outgoing
    # --------
    def fired_slot_index(self):
        self.publisher.publish_check(PyroShared.OUTGOING_PREFIX + PyroTrackActions.FIRED_SLOT_INDEX, {
            "trackindex": self.trackindex,
            "slotindex": self.get_reference().fired_slot_index})

    def playing_slot_index(self):
        self.publisher.publish_check(PyroShared.OUTGOING_PREFIX + PyroTrackActions.PLAYING_SLOT_INDEX, {
            "trackindex": self.trackindex,
            "slotindex": self.get_reference().playing_slot_index})
