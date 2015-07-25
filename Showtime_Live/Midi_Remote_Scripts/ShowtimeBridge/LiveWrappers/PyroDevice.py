from PyroWrapper import *
from PyroDeviceParameter import PyroDeviceParameter


class PyroDevice(PyroWrapper):
    # Message types
    DEVICE_UPDATED = "device_parameters_updated"
    
    # -------------------
    # Wrapper definitions
    # -------------------
    def create_listeners(self):
        if self.handle():
            self.handle().add_parameters_listener(self.parameters_updated)

    def destroy_listeners(self):
        if self.handle():
            self.handle().remove_parameters_listener(self.parameters_updated)

    @classmethod
    def register_methods(cls):
        PyroWrapper.add_outgoing_method(PyroDevice.DEVICE_UPDATED)

    # --------
    # Outgoing
    # --------
    def parameters_updated(self):
        self.update(PyroDevice.DEVICE_UPDATED, {
            "track": self.track.name,
            "device": self.handle().name})

    # ---------
    # Utilities
    # ---------
    def update_hierarchy(self):   
        Log.write("Parameter list changed")
        PyroWrapper.update_hierarchy(self, PyroDeviceParameter, self.handle().parameters)