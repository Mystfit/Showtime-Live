from PyroWrapper import *
from PyroDeviceParameter import PyroDeviceParameter


class PyroDevice(PyroWrapper):
    # Message types
    DEVICE_UPDATED = "device_parameters_updated"
    
    # -------------------
    # Wrapper definitions
    # -------------------
    def create_listeners(self):
        try:
            self.handle().add_parameters_listener(self.parameters_updated)
        except RuntimeError:
            Log.write("Couldn't add listeners to device")

    def destroy_listeners(self):
        try:
            self.handle().remove_parameters_listener(self.parameters_updated)
        except RuntimeError:
            Log.write("Couldn't remove listeners from device")

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
        PyroWrapper.update_hierarchy(self, PyroDeviceParameter, self.handle().parameters)