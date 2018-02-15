from LiveWrapper import *
from ..Utils import Utils

import showtime
from showtime import ZstURI


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

    def __init__(self, name, handle, handleindex=None):
        self.usePlayingPos = True
        self.clip_status_plug = None
        self.clip_notes_updated_plug = None
        self.clip_playing_position_plug = None
        self.clip_trigger_plug = None
        self.clip_notes_set_plug = None
        self.clip_broadcast_playing_pos_plug = None
        LiveWrapper.__init__(self, handle, handleindex)

    @staticmethod
    def build_name(handle, handle_index):
        return "{0}-{1}".format(handle.name)

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

        # Outputs
        # -------
        self.clip_status_plug = self.create_output_plug("clip_status", showtime.ZST_INT)
        self.clip_notes_updated_plug = self.create_output_plug("clip_notes_updated", showtime.ZST_INT)
        self.clip_playing_position_plug = self.create_output_plug("clip_playing_position", showtime.ZST_FLOAT)

        # Inputs
        # ------
        self.clip_trigger_plug = self.create_input_plug("clip_trigger", showtime.ZST_INT)
        self.clip_notes_set_plug = self.create_input_plug("clip_set_notes", showtime.ZST_INT)
        self.clip_broadcast_playing_pos_plug = self.create_input_plug("clip_broadcast_playing_position", showtime.ZST_INT)

    def destroy_plugs(self):
        LiveWrapper.destroy_plugs(self)
        self.remove_plug(self.clip_status_plug)
        self.remove_plug(self.clip_notes_updated_plug)
        self.remove_plug(self.clip_playing_position_plug)
        self.remove_plug(self.clip_trigger_plug)
        self.remove_plug(self.clip_notes_set_plug)
        self.remove_plug(self.clip_broadcast_playing_pos_plug)

        self.clip_status_plug = None
        self.clip_notes_updated_plug = None
        self.clip_playing_position_plug = None
        self.clip_trigger_plug = None
        self.clip_notes_set_plug = None
        self.clip_broadcast_playing_pos_plug = None

    def compute(self, plug):
        if ZstURI.equal(plug.get_URI(), self.clip_trigger_plug.get_URI()):
            self.recv_trigger()
        elif ZstURI.equal(plug.get_URI(), self.clip_notes_set_plug.get_URI()):
            self.recv_notes()
        elif ZstURI.equal(plug.get_URI(), self.clip_broadcast_playing_pos_plug.get_URI()):
            self.recv_broadcast_playing_pos()

    def recv_trigger(self):
        Log.info("LIVE: Clip received trigger message")
        self.handle().fire()

    def recv_notes(self):
        Log.info("LIVE: Clip received notes set message")
        notes = []
        winding = 3

        for note_index in range(plug.size()) / winding:
            note_pitch = plug.int_at(note_index)
            note_start = plug.float_at(note_index+1)
            note_end = plug.float_at(note_index+2)
            notes.append((note_pitch, note_start, note_end))

        self.handle().set_notes(notes)

    def recv_broadcast_playing_pos(self):
        Log.info("LIVE: Clip received set broadcast position message")
        self.wrapper.usePlayingPos = bool(plug.int_at(0))

    # --------
    # Outgoing
    # --------
    def notes_updated(self):
        notes = self.handle().get_notes(0.0, 0, self.handle().length, 127)
        for note in notes:
            for note_info in note:
                Log.info(note_info)
                Log.info(type(note_info))
                self.clip_notes_updated_plug.append_float(float(note_info))
        self.clip_notes_updated_plug.fire()

    def playing_position(self):
        self.clip_playing_position_plug.append(
            Utils.truncate_float(self.handle().playing_position, 4))
        self.clip_playing_position_plug.fire()


    # ---------
    # Hierarchy
    # ---------

    def refresh_hierarchy(self, postactivate):
        pass
