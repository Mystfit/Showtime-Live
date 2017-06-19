from LiveWrapper import *
from ..Utils import Utils


class LiveClip(LiveWrapper):
    # OLD SHOWTIME - Message types
    # --------------------------
    # CLIP_STATUS = "clip_status"
    # CLIP_TRIGGER = "clip_trigger"
    # CLIP_NOTES_UPDATED = "clip_notes_updated"
    # CLIP_NOTES_SET = "clip_notes_set"
    # CLIP_PLAYING_POSITION = "clip_playing_pos"
    # CLIP_BROADCAST_PLAYING_POSITION = "clip_broadcast_playing_pos"
    
    # -------------------
    # Wrapper definitions
    # -------------------

    def __init__(self, handle, handleindex=None, parent=None):
        LiveWrapper.__init__(self, handle, handleindex, parent)
        self.usePlayingPos = True

    def create_handle_id(self):
        return "%scl%s" % (self.parent().id(), self.handleindex)

    def create_plugs(self):
        pass

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

    # --------
    # Outgoing
    # --------
    def notes_updated(self):
        pass
        # self.respond(LiveClip.CLIP_NOTES_UPDATED, self.handle().get_notes(0.0, 0, self.handle().length, 127))

    def playing_position(self):
        pass
        #self.update(LiveClip.CLIP_PLAYING_POSITION, Utils.truncate_float(self.handle().playing_position, 4))

    # --------
    # Incoming
    # --------
    @staticmethod
    def queue_broadcast_playing_pos(args):
        instance = LiveClip.find_wrapper_by_id(args["id"])
        instance.usePlayingPos = args["value"]

    @staticmethod
    def queue_clip_trigger(args):
        instance = LiveClip.find_wrapper_by_id(args["id"])
        instance.handle().fire()

    @staticmethod
    def queue_clip_notes_set(args):
        instance = LiveClip.find_wrapper_by_id(args["id"])
        instance.handle().set_notes()

    @staticmethod
    def queue_clip_notes_set(args):
        instance = LiveClip.find_wrapper_by_id(args["id"])
        if instance:
            instance.apply_clip_notes_set(args["value"])
        else:
            Log.warn("Could not find Clip %s " % instance.name)

    def apply_clip_notes_set(self, value):
        self.handle().set_notes(value)
        Log.info("Clip notes:%s on %s" % (self.handle().value, self.id()))
