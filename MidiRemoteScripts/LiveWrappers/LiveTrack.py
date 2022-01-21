from ShowtimeLive.LiveWrappers.LiveClipslot import LiveClipslot
from ShowtimeLive.LiveWrappers.LiveDevice import LiveDevice
from ShowtimeLive.LiveWrappers.LiveChain import LiveChain
from ShowtimeLive.LiveWrappers.LiveWrapper import LiveWrapper
from ShowtimeLive.Logger import Log
from ShowtimeLive.Utils import Utils
from ShowtimeLive.showtimeAPI import API as ZST
import ShowtimeLive.showtimeAPI as showtime


class LiveTrack(LiveWrapper):
    # Message types
    # TRACK_METER = "track_meter"
    # TRACK_STOP = "track_stop"
    # TRACK_MIXER_SENDS_UPDATED = "track_sends_updated"
    # TRACK_PLAYING_NOTES = "track_playing_notes"
    # NOTE_ON = "on"
    # NOTE_OFF = "off"

    def __init__(self, name, handle, handleindex):
        LiveWrapper.__init__(self, name, handle, handleindex)
        self.lastplaypos = None
        self.playingnotes = set()
        self.devices = ZST.ZstComponent("devices")
        self.clipslots = ZST.ZstComponent("clipslots")
        showtime.client().register_entity(self.devices)
        showtime.client().register_entity(self.clipslots)

    def on_registered(self, entity):
        LiveWrapper.on_registered(self, entity)
        self.component.add_child(self.devices)
        self.component.add_child(self.clipslots)

    # ------
    # Naming
    # ------

    @staticmethod
    def build_name(handle, handle_index):
        return handle.name


    # -------------------
    # Wrapper definitions
    # -------------------
    def create_listeners(self):
        LiveWrapper.create_listeners(self)
        if self.handle():
            try:
                Log.write("Registering device listeners for {0}".format(self.handle().name))
                self.handle().add_devices_listener(self.refresh_devices)
            except Exception as e:
                Log.error("Failed to create track listeners for {0}: {1}".format(self.handle().name, e))

            try:
                Log.write("Registering clipslot listeners for {0}".format(self.handle().name))
                self.handle().add_fired_slot_index_listener(self.clip_status_fired)
                self.handle().add_playing_slot_index_listener(self.clip_status_playing)
                self.handle().add_clip_slots_listener(self.refresh_clipslots)
            except Exception as e:
                pass
        else:
            Log.warn("No handle found for track")

    def destroy_listeners(self):
        LiveWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_devices_listener(self.refresh_devices)
            except Exception as e:
                Log.error("Failed to remove track listeners: {0}".format(e))

            try:
                self.handle().remove_fired_slot_index_listener(self.clip_status_fired)
                self.handle().remove_playing_slot_index_listener(self.clip_status_triggered)
                self.handle().remove_clip_slots_listener(self.refresh_clips)
            except Exception as e:
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

    def clip_status_fired(self):
        pass

    def clip_status_playing(self):
        pass


    # ---------
    # Hierarchy
    # ---------
    def refresh_devices(self, postactivate=True):
        Log.write("{0} - Device list changed".format(self.component.URI().last().path()))
        if hasattr(self.handle(), "devices"):
            LiveWrapper.update_hierarchy(self.devices, LiveDevice, self.handle().devices, postactivate)

    def refresh_clipslots(self, postactivate=True):
        Log.write("{0} - Clip slots changed".format(self.component.URI().last().path()))
        if hasattr(self.handle(), "clip_slots"):
            LiveWrapper.update_hierarchy(self.clipslots, LiveClipslot, self.handle().clip_slots, postactivate)

    def refresh_hierarchy(self, postactivate):
        self.refresh_devices(postactivate)
        self.refresh_clipslots(postactivate)


    # ---------
    # Utilities
    # ---------

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

