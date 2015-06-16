from PyroWrapper import *

class PyroDevice(PyroWrapper):
    # Message types
    DEVICE_UPDATED = "device_parameters_updated"

    def __init__(self, deviceindex, handle, parent):
        PyroWrapper.__init__(self, handle)
        self.deviceindex = deviceindex
        self.handle().add_parameters_listener(self.parameters_updated)

    @classmethod
    def register_methods(cls):
        PyroWrapper.add_outgoing_method(PyroDevice.DEVICE_UPDATED)

    def parameters_updated(self):
        self.update(PyroDevice.DEVICE_UPDATED, {
            "track": self.track.name,
            "device": self.handle().name})
