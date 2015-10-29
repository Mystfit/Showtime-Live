from PyroWrapper import *
from ..Utils import Utils


class PyroClip(PyroWrapper):
    # Message types
    CLIP_STATUS = "clip_status"
    CLIP_TRIGGER = "clip_trigger"
    CLIP_NOTES_UPDATED = "clip_notes_updated"
    
    # -------------------
    # Wrapper definitions
    # -------------------

    def create_handle_id(self):
        return "%scl%s" % (self.parent().id(), self.handleindex)

    def create_listeners(self):
        PyroWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_notes_listener(self.notes_updated)

    def destroy_listeners(self):
        PyroWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_notes_listener(self.notes_updated)
            except RuntimeError:
                Log.warn("Couldn't remove clip listeners")

    @classmethod
    def register_methods(cls):
        PyroWrapper.add_outgoing_method(PyroClip.CLIP_STATUS)
        PyroWrapper.add_outgoing_method(PyroClip.CLIP_NOTES_UPDATED)
        PyroWrapper.add_incoming_method(PyroClip.CLIP_TRIGGER, ["id"], PyroClip.queue_clip_trigger)

    def to_object(self):
        params = PyroWrapper.to_object(self)

        # Use track as parent rather than clipslot
        params.update({
            "index": self.parent().handleindex,
            "parent": self.parent().parent().id(),
            "notes": self.handle().get_notes(0.0, 0, self.handle().length, 127)
        })

        return params

    # --------
    # Outgoing
    # --------
    def notes_updated(self):
        self.update(PyroClip.CLIP_NOTES_UPDATED, self.handle().get_notes(0.0, 0, self.handle().length, 127))

    # --------
    # Incoming
    # --------
    @staticmethod
    def queue_clip_trigger(args):
        instance = PyroClip.find_wrapper_by_id(args["id"])
        instance.handle().fire()

    # ---------
    # Utilities
    # ---------