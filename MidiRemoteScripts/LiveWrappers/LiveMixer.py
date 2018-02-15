from LiveWrapper import *

# TODO: Update mixer
class LiveMixer(LiveWrapper):
    # Message types
    MIXER_SENDS_UPDATED = "mixer_sends_updated"
    # MIXER_VOLUME_SET = "mixer_volume_set"
    # MIXER_VOLUME_UPDATED = "mixer_volume_updated"

    @staticmethod
    def build_name(handle, handle_index):
        return "mixer-{0}".format(handle_index)

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
        pass

    # ---------
    # Utilities
    # ---------
    def refresh_hierarchy(self, postactivate):
        Log.info("Send list changed")
