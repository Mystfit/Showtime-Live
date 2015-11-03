from PyroWrapper import *
from ..Utils import Utils


class PyroClip(PyroWrapper):
    # Message types
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
        PyroWrapper.__init__(self, handle, handleindex, parent)
        self.usePlayingPos = True

    def create_handle_id(self):
        return "%scl%s" % (self.parent().id(), self.handleindex)

    def create_listeners(self):
        PyroWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_playing_position_listener(self.playing_position)
            if self.handle().is_midi_clip:
                self.handle().add_notes_listener(self.notes_updated)


    def destroy_listeners(self):
        PyroWrapper.destroy_listeners(self)
        if self.handle():
            self.handle().remove_playing_position_listener(self.playing_position)
            if self.handle().is_midi_clip:
                self.handle().remove_notes_listener(self.notes_updated)

    @classmethod
    def register_methods(cls):
        PyroWrapper.add_outgoing_method(PyroClip.CLIP_STATUS)
        PyroWrapper.add_outgoing_method(PyroClip.CLIP_NOTES_UPDATED)
        PyroWrapper.add_outgoing_method(PyroClip.CLIP_PLAYING_POSITION)
        PyroWrapper.add_incoming_method(PyroClip.CLIP_TRIGGER, ["id"], PyroClip.queue_clip_trigger)
        PyroWrapper.add_incoming_method(PyroClip.CLIP_NOTES_SET, ["id"], PyroClip.queue_clip_notes_set)
        PyroWrapper.add_incoming_method(PyroClip.CLIP_BROADCAST_PLAYING_POSITION, ["id"], PyroClip.queue_broadcast_playing_pos)


    def to_object(self):
        params = PyroWrapper.to_object(self)

        # Use track as parent rather than clipslot
        params.update({
            "index": self.parent().handleindex,
            "parent": self.parent().parent().id(),
            "notes": self.handle().get_notes(0.0, 0, self.handle().length, 127) if(self.handle().is_midi_clip) else None
        })

        return params

    # --------
    # Outgoing
    # --------
    def notes_updated(self):
        self.update(PyroClip.CLIP_NOTES_UPDATED, self.handle().get_notes(0.0, 0, self.handle().length, 127))

    def playing_position(self):
        self.update(PyroClip.CLIP_PLAYING_POSITION, Utils.truncate_float(self.handle().playing_position, 4))

    # --------
    # Incoming
    # --------
    @staticmethod
    def queue_broadcast_playing_pos(args):
        instance = PyroClip.find_wrapper_by_id(args["id"])
        instance.usePlayingPos = args["value"]

    @staticmethod
    def queue_clip_trigger(args):
        instance = PyroClip.find_wrapper_by_id(args["id"])
        instance.handle().fire()

    @staticmethod
    def queue_clip_notes_set(args):
        instance = PyroClip.find_wrapper_by_id(args["id"])
        instance.handle().set_notes()

    @staticmethod
    def queue_clip_notes_set(args):
        instance = PyroClip.find_wrapper_by_id(args["id"])
        if instance:
            instance.defer_action(instance.apply_clip_notes_set, args["value"])
        else:
            Log.warn("Could not find Clip %s " % instance.name)

    def apply_clip_notes_set(self, value):
        self.handle().set_notes(value)
        Log.info("Clip notes:%s on %s" % (self.handle().value, self.id()))

    # ---------
    # Utilities
    # ---------