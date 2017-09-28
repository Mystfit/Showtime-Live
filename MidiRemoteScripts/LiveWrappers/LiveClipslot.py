from LiveClip import LiveClip
from LiveWrapper import *


class LiveClipslot(LiveWrapper):
    def create_handle_id(self):
        return "%scs%s" % (self.parent().id(), self.handleindex)

    def name(self):
        return self.id()

    # -------------------
    # Wrapper definitions
    # -------------------
    def create_listeners(self):
        LiveWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_has_clip_listener(self.update_hierarchy)
            self.handle().add_is_triggered_listener(self.clip_slot_status)
            self.handle().add_playing_status_listener(self.clip_slot_status)

    def destroy_listeners(self):
        LiveWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_has_clip_listener(self.update_hierarchy)
                self.handle().remove_is_triggered_listener(self.clip_slot_status)
                self.handle().remove_playing_status_listener(self.clip_slot_status)
            except (RuntimeError, AttributeError):
                Log.warn("Couldn't remove clipslot listeners")

    def update_hierarchy(self):
        clip = [self.handle().clip] if self.handle().clip else []
        LiveWrapper.update_hierarchy(self, LiveClip, clip)

    # --------
    # Outgoing
    # --------
    def clip_slot_status(self):
        for clip in self.children():
            pass
            #clip.update(LiveClip.CLIP_STATUS, {"triggered": self.handle().is_triggered, "playing": self.handle().is_playing})
