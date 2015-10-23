from PyroWrapper import *
from PyroClip import PyroClip
from ..Utils import Utils


class PyroClipslot(PyroWrapper):
    
    def create_handle_id(self):
        return "%scs%s" % (self.parent().id(), self.handleindex)

    # -------------------
    # Wrapper definitions
    # -------------------
    def create_listeners(self):
        PyroWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_has_clip_listener(self.update_hierarchy)
            self.handle().add_is_triggered_listener(self.clip_slot_status)
            self.handle().add_playing_status_listener(self.clip_slot_status)

    def destroy_listeners(self):
        PyroWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_has_clip_listener(self.update_hierarchy)
                self.handle().remove_is_triggered_listener(self.clip_slot_status)
                self.handle().remove_playing_status_listener(self.clip_slot_status)
            except RuntimeError:
                Log.warn("Couldn't remove clipslot listeners")

    @classmethod
    def register_methods(cls):
        pass

    def update_hierarchy(self):
        clip = [self.handle().clip] if self.handle().clip else []
        PyroWrapper.update_hierarchy(self, PyroClip, clip)

    # --------
    # Outgoing
    # --------
    def clip_slot_status(self):
        for clip in self.children():
            clip.update(PyroClip.CLIP_STATUS, {"triggered": self.handle().is_triggered, "playing": self.handle().is_playing})

    # --------
    # Incoming
    # --------

    # ---------
    # Utilities
    # ---------