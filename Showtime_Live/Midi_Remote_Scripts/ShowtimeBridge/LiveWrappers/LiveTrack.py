from LiveClipslot import LiveClipslot
from LiveDevice import LiveDevice
from LiveSend import LiveSend
from LiveWrapper import *
from ..Utils import Utils


class LiveTrack(LiveWrapper):
    # Message types
    TRACK_METER = "track_meter"
    TRACK_STOP = "track_stop"
    TRACK_MIXER_SENDS_UPDATED = "track_sends_updated"

    # -------------------
    # Wrapper definitions
    # -------------------
    def create_listeners(self):
        LiveWrapper.create_listeners(self)
        if self.handle():
            try:
                self.handle().mixer_device.add_sends_listener(self.update_sends)
                self.handle().add_clip_slots_listener(self.update_clips)
                self.handle().add_fired_slot_index_listener(self.clip_status_fired)
                self.handle().add_playing_slot_index_listener(self.clip_status_playing)
            except (RuntimeError, AttributeError):
                pass
            self.handle().add_devices_listener(self.update_devices)

    def destroy_listeners(self):
        LiveWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().mixer_device.remove_sends_listener(self.update_sends())
                self.handle().remove_clip_slots_listener(self.update_clips)
                self.handle().remove_fired_slot_index_listener(self.clip_status_fired)
                self.handle().remove_playing_slot_index_listener(self.clip_status_triggered)
            except (RuntimeError, AttributeError):
                pass
            self.handle().remove_devices_listener(self.update_devices)    
        
    @classmethod
    def register_methods(cls):
        cls.add_outgoing_method(LiveTrack.TRACK_METER)
        cls.add_outgoing_method(LiveTrack.TRACK_MIXER_SENDS_UPDATED)
        cls.add_incoming_method(LiveTrack.TRACK_STOP, ["id"], LiveTrack.stop_track)

    def to_object(self):
        params = {
            "armed": (self.handle().arm if self.handle().can_be_armed else False),
            "solo": self.handle().solo,
            "color": self.handle().color,
            "mute": self.handle().mute,
            "midi": self.handle().has_midi_input,
        }
        return LiveWrapper.to_object(self, params)

    # --------
    # Incoming
    # --------
    @staticmethod
    def fire_slot_index(args):
        track = LiveTrack.find_wrapper_by_id(args["id"]).handle()
        try:
            track.clip_slots[int(args["clipindex"])].fire()
        except AttributeError:
            Log.warn("No clip slots in track")

    @staticmethod
    def stop_track(args):
        track = LiveTrack.find_wrapper_by_id(args["id"]).handle()
        try:
            track.stop_all_clips()
        except AttributeError:
            Log.warn("No clip slots in track")

    # --------
    # Outgoing
    # --------
    def output_meter(self):
        self.update(LiveTrack.TRACK_METER, {"peak": Utils.truncate(((self.handle().output_meter_left + self.handle().output_meter_right) * 0.5), 4)})

    # ---------
    # Utilities
    # ---------
    def update_hierarchy(self):   
        self.update_devices()
        self.update_clips()
        self.update_sends()

    def update_devices(self):
        Log.info("%s - Device list changed" % self.id())
        LiveWrapper.update_hierarchy(self, LiveDevice, self.handle().devices)

    def update_clips(self):
        Log.info("%s - Clip slots changed" % self.id())
        LiveWrapper.update_hierarchy(self, LiveClipslot, self.handle().clip_slots)

    def update_sends(self):
        Log.info("%s - Sends changed" % self.id())
        LiveWrapper.update_hierarchy(self, LiveSend, self.handle().mixer_device.sends)
