from LiveWrapper import *
from LiveDeviceParameter import LiveDeviceParameter


class LiveDevice(LiveWrapper):
    # Message types
    DEVICE_UPDATED = "device_parameters_updated"
    
    # -------------------
    # Wrapper definitions
    # -------------------
    def create_listeners(self):
        LiveWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_parameters_listener(self.parameters_updated)

    def destroy_listeners(self):
        LiveWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_parameters_listener(self.parameters_updated)
            except RuntimeError:
                Log.warn("Couldn't remove device listener")

    @classmethod
    def register_methods(cls):
        LiveWrapper.add_outgoing_method(LiveDevice.DEVICE_UPDATED)

    def to_object(self):
        params = {
            "can_have_drum_pads": self.handle().can_have_drum_pads,
            "can_have_chains": self.handle().can_have_chains
        }
        return LiveWrapper.to_object(self, params)

    # --------
    # Outgoing
    # --------
    def parameters_updated(self):
        for parameter in self._children:
            parameter.destroy()

        self.update(LiveDevice.DEVICE_UPDATED, {
            "track": self.track.name,
            "device": self.handle().name})

    # ---------
    # Utilities
    # ---------
    def update_hierarchy(self):   
        Log.info("--- Parameter list changed")
        LiveWrapper.update_hierarchy(self, LiveDeviceParameter, self.handle().parameters)