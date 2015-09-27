from PyroWrapper import *
from PyroDevice import PyroDevice
from PyroSend import PyroSend


class PyroTrack(PyroWrapper):
    # Message types
    TRACK_FIRED_SLOT = "track_fired_slot"
    TRACK_PLAYING_SLOT = "track_playing_slot"
    TRACK_METER = "track_meter"
    TRACK_FIRE_SLOT_INDEX = "track_fire_slot_index"
    TRACK_STOP = "track_stop"

    # -------------------
    # Wrapper definitions
    # -------------------
    def create_listeners(self):
        PyroWrapper.create_listeners(self)
        if self.handle():
            try:
                self.handle().add_fired_slot_index_listener(self.fired_slot_index)
                self.handle().add_playing_slot_index_listener(self.playing_slot_index)
                self.handle().add_devices_listener(self.update_hierarchy)
            except:
                Log.warn("Couldn't add listeners to track")

    def destroy_listeners(self):
        PyroWrapper.destroy_listeners(self)
        if self.handle():
            self.handle().remove_fired_slot_index_listener(self.fired_slot_index)
            self.handle().remove_playing_slot_index_listener(self.playing_slot_index)
            self.handle().remove_devices_listener(self.update_hierarchy)    
        else:
            Log.warn("Handle is gone. Can't remove listeners.")   
        
    @classmethod
    def register_methods(cls):
        PyroWrapper.add_outgoing_method(PyroTrack.TRACK_FIRED_SLOT)
        PyroWrapper.add_outgoing_method(PyroTrack.TRACK_METER)
        PyroWrapper.add_outgoing_method(PyroTrack.TRACK_PLAYING_SLOT)
        PyroWrapper.add_incoming_method(PyroTrack.TRACK_FIRE_SLOT_INDEX, ["id", "clipindex"], PyroTrack.fire_slot_index)
        PyroWrapper.add_incoming_method(PyroTrack.TRACK_STOP, ["id"], PyroTrack.stop_track)

    # --------
    # Incoming
    # --------
    @staticmethod
    def fire_slot_index(args):
        track = PyroTrack.findById(args["id"]).handle()
        try:
            track.clip_slots[int(args["clipindex"])].fire()
        except AttributeError:
            Log.warn("No clip slots in track")

    @staticmethod
    def stop_track(args):
        track = PyroTrack.findById(args["id"]).handle()
        try:
            track.stop_all_clips()
        except AttributeError:
            Log.warn("No clip slots in track")

    # --------
    # Outgoing
    # --------
    def fired_slot_index(self):
        self.update(PyroTrack.TRACK_FIRED_SLOT, {
            "trackindex": self.handleindex,
            "slotindex": self.handle().fired_slot_index
        })

    def playing_slot_index(self):
        self.update(PyroTrack.TRACK_PLAYING_SLOT, {
            "trackindex": self.handleindex,
            "slotindex": self.handle().playing_slot_index})

    def output_meter(self):
        self.update(PyroTrack.TRACK_METER, {
            "trackindex": self.handleindex,
            "peak": (self.handle().output_meter_left + self.handle().output_meter_right) * 0.5})

    # ---------
    # Utilities
    # ---------
    def update_hierarchy(self):   
        Log.info("Device list changed")
        PyroWrapper.update_hierarchy(self, PyroDevice, self.handle().devices)
