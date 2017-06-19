from LiveSend import LiveSend
from LiveWrapper import *

# TODO: Update mixer
class LiveMixer(LiveWrapper):
    # Message types
    MIXER_SENDS_UPDATED = "mixer_sends_updated"
    # MIXER_VOLUME_SET = "mixer_volume_set"
    # MIXER_VOLUME_UPDATED = "mixer_volume_updated"


    def create_handle_id(self):
        return "%sm0" % self.parent().id()
    
    # -------------------
    # Wrapper definitions
    # -------------------
    def create_listeners(self):
        LiveWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_sends_listener(self.sends_updated)

    def destroy_listeners(self):
        LiveWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_sends_listener(self.sends_updated)
            except (RuntimeError, AttributeError):
                Log.warn("Couldn't remove sends listener")

    # --------
    # Outgoing
    # --------
    def sends_updated(self):
        self.update_hierarchy()

    # ---------
    # Utilities
    # ---------
    def update_hierarchy(self):   
        Log.info("Send list changed")
        LiveWrapper.update_hierarchy(self, LiveSend, self.handle().sends)
