from PyroWrapper import *
from ..Utils import Utils


class PyroClip(PyroWrapper):
    # Message types
    CLIP_STATUS = "clip_status"
    CLIP_TRIGGER = "clip_trigger"
    
    # -------------------
    # Wrapper definitions
    # -------------------
    def create_listeners(self):
        PyroWrapper.create_listeners(self)
        if self.handle():
            pass

    def destroy_listeners(self):
        PyroWrapper.destroy_listeners(self)
        if self.handle():
            try:
                pass
            except RuntimeError:
                Log.warn("Couldn't remove clip listeners")

    @classmethod
    def register_methods(cls):
        PyroWrapper.add_outgoing_method(PyroClip.CLIP_STATUS)
        PyroWrapper.add_incoming_method(PyroClip.CLIP_TRIGGER, ["id"], PyroClip.queue_clip_trigger)

    @staticmethod
    def queue_clip_trigger(args):
        instance = PyroClip.find_wrapper_by_id(args["id"])
        instance.handle().fire()

    # --------
    # Outgoing
    # --------

    # --------
    # Incoming
    # --------

    # ---------
    # Utilities
    # ---------