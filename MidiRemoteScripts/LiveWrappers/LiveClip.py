from LiveWrapper import *
from ..Utils import Utils

import showtime
from showtime import Showtime as ZST
from showtime import ZstURI, ZstPlugDataEventCallback


# Wrapper
# -------
class LiveClip(LiveWrapper):
    # SHOWTIME - Message types
    # --------------------------
    CLIP_STATUS = "clip_status"
    CLIP_TRIGGER = "clip_trigger"
    CLIP_NOTES_UPDATED = "clip_notes_updated"
    CLIP_NOTES_SET = "clip_notes_set"
    CLIP_PLAYING_POSITION = "clip_playing_pos"
    CLIP_BROADCAST_PLAYING_POSITION = "clip_broadcast_playing_pos"
    
    # -------------------
    # Wrapper definitions
    # -------------------

    def __init__(self, handle, handleindex=None, parent=None):
        LiveWrapper.__init__(self, handle, handleindex, parent)
        self.usePlayingPos = True

    def create_handle_id(self):
        return "%scl%s" % (self.parent().id(), self.handleindex)

    def create_listeners(self):
        LiveWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_playing_position_listener(self.playing_position)
            if self.handle().is_midi_clip:
                self.handle().add_notes_listener(self.notes_updated)

    def destroy_listeners(self):
        LiveWrapper.destroy_listeners(self)
        if self.handle():
            self.handle().remove_playing_position_listener(self.playing_position)
            if self.handle().is_midi_clip:
                self.handle().remove_notes_listener(self.notes_updated)

    def create_plugs(self):
        LiveWrapper.create_plugs(self)

        if not self.showtime_instrument:
            Log.warn("No showtime_instrument string set. Value is {0}".format(self.showtime_instrument))
            return

        # Outputs
        # -------
        self.clip_status_plug = ZST.create_output_plug(
            ZstURI(
                "ableton_perf",
                self.showtime_instrument,
                "clip_status"),
            showtime.ZST_INT)

        self.clip_notes_updated_plug = ZST.create_output_plug(
            ZstURI(
                "ableton_perf",
                self.showtime_instrument,
                "clip_notes_updated"),
            showtime.ZST_INT)

        self.clip_playing_position_plug = ZST.create_output_plug(
            ZstURI(
                "ableton_perf",
                self.showtime_instrument,
                "clip_playing_position"),
            showtime.ZST_FLOAT)

        # Inputs
        # ------
        self.clip_trigger_plug = ZST.create_input_plug(
            ZstURI(
                "ableton_perf",
                self.showtime_instrument,
                "clip_trigger"),
            showtime.ZST_INT)
        self.clip_trigger_callback = ClipTriggerCallback()
        self.clip_trigger_callback.set_wrapper(self)
        self.clip_trigger_plug.input_events().attach_event_callback(
            self.clip_trigger_callback)

        self.clip_notes_set_plug = ZST.create_input_plug(
            ZstURI(
                "ableton_perf",
                self.showtime_instrument,
                "clip_set_notes"),
            showtime.ZST_INT)
        self.clip_notes_set_callback = ClipNotesSetCallback()
        self.clip_notes_set_callback.set_wrapper(self)
        self.clip_notes_set_plug.input_events().attach_event_callback(
            self.clip_notes_set_callback)

        self.clip_broadcast_playing_pos_plug = ZST.create_input_plug(
            ZstURI(
                "ableton_perf",
                self.showtime_instrument,
                "clip_broadcast_playing_position"),
            showtime.ZST_INT)
        self.clip_broadcast_playing_pos_callback = ClipBroadCastPlayingPosCallback()
        self.clip_broadcast_playing_pos_callback.set_wrapper(self)
        self.clip_broadcast_playing_pos_plug.input_events().attach_event_callback(
            self.clip_broadcast_playing_pos_callback)

    def destroy_plugs(self):
        LiveWrapper.destroy_plugs(self)
        ZST.destroy_plug(self.clip_status_plug)
        ZST.destroy_plug(self.clip_notes_updated_plug)
        ZST.destroy_plug(self.clip_playing_position_plug)
        ZST.destroy_plug(self.clip_trigger_plug)
        ZST.destroy_plug(self.clip_notes_set_plug)
        ZST.destroy_plug(self.clip_broadcast_playing_pos_plug)
        self.clip_trigger_callback = None
        self.clip_notes_set_callback = None
        self.clip_broadcast_playing_pos_callback = None

    # --------
    # Outgoing
    # --------
    def notes_updated(self):
        notes = self.handle().get_notes(0.0, 0, self.handle().length, 127)
        for note in notes:
            for note_info in note:
                self.clip_notes_updated_plug.values().append(note_info)
        self.clip_notes_updated_plug.fire()
        self.clip_notes_updated_plug.values().clear()

    def playing_position(self):
        self.clip_playing_position_plug.values().append(
            Utils.truncate_float(self.handle().playing_position, 4))
        self.clip_playing_position_plug.fire()
        self.clip_playing_position_plug.values().clear()


# Callbacks
# ---------
class ClipTriggerCallback(ZstPlugDataEventCallback):
    def set_wrapper(self, wrapper):
        self.wrapper = wrapper

    def run(self, plug):
        Log.info("LIVE: Clip received trigger message")
        self.wrapper.handle().fire()


class ClipNotesSetCallback(ZstPlugDataEventCallback):
    def set_wrapper(self, wrapper):
        self.wrapper = wrapper

    def run(self, plug):
        Log.info("LIVE: Clip received notes set message")
        notes = []
        winding = 3
        
        for note_index in range(plug.values().size()) / winding:
            note_pitch = plug.values().int_at(note_index)
            note_start = plug.values().float_at(note_index+1)
            note_end = plug.values().float_at(note_index+2)
            notes.append((note_pitch, note_start, note_end))

        self.wrapper.handle().set_notes(notes)


class ClipBroadCastPlayingPosCallback(ZstPlugDataEventCallback):
    def set_wrapper(self, wrapper):
        self.wrapper = wrapper

    def run(self, plug):
        Log.info("LIVE: Clip received set broadcast position message")
        self.wrapper.usePlayingPos = bool(plug.values().int_at(0))

