from PyroWrapper import *

class PyroTrack(PyroWrapper):
    # Message types
    TRACK_FIRED_SLOT = "track_fired_slot"
    TRACK_PLAYING_SLOT = "track_playing_slot"
    TRACK_METER = "track_meter"
    TRACK_FIRE_SLOT_INDEX = "track_fire_slot_index"
    TRACK_STOP = "track_stop"

    def __init__(self, trackindex, handle, parent):
        PyroWrapper.__init__(self, handle, parent)
        self.trackindex = trackindex
        self.devices = []
        self.sends = []

        # Listeners
        self.handle().add_fired_slot_index_listener(self.fired_slot_index)
        self.handle().add_playing_slot_index_listener(self.playing_slot_index)

    @classmethod
    def register_methods(cls):
        PyroWrapper.add_outgoing_method(PyroTrack.TRACK_FIRED_SLOT)
        PyroWrapper.add_outgoing_method(PyroTrack.TRACK_METER)
        PyroWrapper.add_outgoing_method(PyroTrack.TRACK_PLAYING_SLOT)
        PyroWrapper.add_incoming_method(PyroTrack.TRACK_FIRE_SLOT_INDEX, ["clipindex"], PyroTrack.fire_slot_index)
        PyroWrapper.add_incoming_method(PyroTrack.TRACK_STOP, ["id"], PyroTrack.stop_track)

    # Incoming
    # --------
    @staticmethod
    def fire_slot_index(args):
        PyroTrack.findById(args["id"]).handle().clip_slots[args["clipindex"]].fire()

    @staticmethod
    def stop_track(args):
        PyroTrack.findById(args["id"]).handle().stop_all_clips()

    # Outgoing
    # --------
    def fired_slot_index(self):
        self.update(PyroTrack.TRACK_FIRED_SLOT, {
            "trackindex": self.trackindex,
            "slotindex": self.handle().fired_slot_index
        })

    def playing_slot_index(self):
        self.update(PyroTrack.TRACK_PLAYING_SLOT, {
            "trackindex": self.trackindex,
            "slotindex": self.handle().playing_slot_index})

    def output_meter(self):
        self.update(PyroTrack.TRACK_METER, {
            "trackindex": self.trackindex,
            "peak": (self.handle().output_meter_left + self.handle().output_meter_right) * 0.5})
