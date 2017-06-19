from LiveWrapper import *
from LiveDeviceParameter import LiveDeviceParameter


class LiveDevice(LiveWrapper):
    
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
            except (RuntimeError, AttributeError):
                Log.warn("Couldn't remove device listener")

    def create_plugs(self):
        pass

    # --------
    # Outgoing
    # --------
    def parameters_updated(self):
        for parameter in self._children:
            parameter.destroy()

    # ---------
    # Utilities
    # ---------
    def update_hierarchy(self):
        Log.info("%s - Parameter list changed" % self.id())
        LiveWrapper.update_hierarchy(self, LiveDeviceParameter, self.handle().parameters)