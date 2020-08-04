from LiveClip import LiveClip
from LiveWrapper import *


class LiveClipslot(LiveWrapper):

    @staticmethod
    def build_name(handle, handle_index):
        return "clipslot-{0}".format(handle_index)

    # -------------------
    # Wrapper definitions
    # -------------------
    def create_listeners(self):
        LiveWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_has_clip_listener(self.refresh_clip)
            self.handle().add_is_triggered_listener(self.clip_slot_status)
            self.handle().add_playing_status_listener(self.clip_slot_status)

    def destroy_listeners(self):
        LiveWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_has_clip_listener(self.refresh_clip)
                self.handle().remove_is_triggered_listener(self.clip_slot_status)
                self.handle().remove_playing_status_listener(self.clip_slot_status)
            except (RuntimeError, AttributeError):
                Log.warn("Couldn't remove clipslot listeners")


    # ---------
    # Hierarchy
    # ---------

    def refresh_clip(self, postactivate=True):
        clip = [self.handle().clip] if self.handle().clip else []
        LiveWrapper.update_hierarchy(self.component, LiveClip, clip, postactivate)

    def refresh_hierarchy(self, postactivate):
        self.refresh_clip(postactivate)

    # --------
    # Outgoing
    # --------
    def clip_slot_status(self):
        for clip in self.children():
            pass
            #clip.update(LiveClip.CLIP_STATUS, {"triggered": self.handle().is_triggered, "playing": self.handle().is_playing})
