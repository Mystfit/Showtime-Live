from LiveClipslot import LiveClipslot
from LiveClip import LiveClip
from LiveDevice import LiveDevice
from LiveSend import LiveSend
from LiveWrapper import *
from ..Utils import Utils


class LiveTrack(LiveWrapper):
    # Message types
    # TRACK_METER = "track_meter"
    # TRACK_STOP = "track_stop"
    # TRACK_MIXER_SENDS_UPDATED = "track_sends_updated"
    # TRACK_PLAYING_NOTES = "track_playing_notes"
    # NOTE_ON = "on"
    # NOTE_OFF = "off"

    # -------------------
    # Wrapper definitions
    # -------------------
    def create_listeners(self):
        LiveWrapper.create_listeners(self)
        if self.handle():
            try:
                self.handle().mixer_device.add_sends_listener(self.update_sends)
                self.handle().add_devices_listener(self.update_devices)
                self.handle().add_clip_slots_listener(self.update_clips)
                self.handle().add_fired_slot_index_listener(self.clip_status_fired)
                self.handle().add_playing_slot_index_listener(self.clip_status_playing)
            except (RuntimeError, AttributeError):
                pass

    def destroy_listeners(self):
        LiveWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().mixer_device.remove_sends_listener(self.update_sends())
                self.handle().remove_devices_listener(self.update_devices)
                self.handle().remove_clip_slots_listener(self.update_clips)
                self.handle().remove_fired_slot_index_listener(self.clip_status_fired)
                self.handle().remove_playing_slot_index_listener(self.clip_status_triggered)
            except (RuntimeError, AttributeError):
                pass
        
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

    def tick(self):
        # Find current playing notes for midi clips on this track
        if self.handle().has_midi_input and self.handle().playing_slot_index > -1:
            # How far to look ahead to reduce perceived latency
            offset = 0.0

            cliphandle = self.handle().clip_slots[self.handle().playing_slot_index].clip
            playposition = cliphandle.playing_position + offset
            if not hasattr(self, "lastplaypos") or self.lastplaypos > playposition:
                self.lastplaypos = 0.0

            # Elapsed time between last tick and now for this clip
            delta = playposition - self.lastplaypos

            # Get slice of notes from the clip based on current play time
            # notes = cliphandle.get_notes(playposition - delta, 0, 0.2, 127)
            notes = cliphandle.get_notes(self.lastplaypos, 0, delta, 127)
            self.lastplaypos = playposition

            if len(notes) > 0:
                changednotes = []

                if not hasattr(self, "playingnotes"):
                    self.playingnotes = set()

                # Determine stopped notes
                Log.info(self.playingnotes)
                stoppednotes = []
                for note in self.playingnotes:
                    if note[1] + note[2] < playposition or note[1] < playposition:
                        stoppednotes.append(note)
                        # changednotes.append({"status": LiveTrack.NOTE_OFF, "note": note})

                #  Remove stopped notes outside of set
                for note in stoppednotes:
                    self.playingnotes.remove(note)

                # Determine new notes not already playing
                for note in notes:
                    if note not in self.playingnotes:
                        self.playingnotes.add(note)
                        # changednotes.append({"status": LiveTrack.NOTE_ON, "note": note})

                # Send note diff to showtime
                if len(changednotes) > 0:
                    # self.update(LiveTrack.TRACK_PLAYING_NOTES, changednotes)
                    pass

