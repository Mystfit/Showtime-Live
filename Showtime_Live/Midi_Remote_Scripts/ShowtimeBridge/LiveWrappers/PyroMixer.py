from PyroWrapper import *


class PyroMixer(PyroWrapper):
    # Message types

    def create_handle_id(self):
        return PyroMixer.format_parameter_id(self.parent().id(), self.handleindex)

    @staticmethod
    def format_parameter_id(parentId, mixerId):
        return str(parentId) + "m" + str(mixerId)
    
    # -------------------
    # Wrapper definitions
    # -------------------
    def create_listeners(self):
        PyroWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_sends_listener(self.sends_updated)

    def destroy_listeners(self):
        PyroWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_sends_listener(self.sends_updated)
            except RuntimeError:
                Log.warn("Couldn't remove sends listener")

    @classmethod
    def register_methods(cls):
        pass
        # PyroWrapper.add_outgoing_method(PyroDevice.MIXER_SENDS_UPDATED)

    # --------
    # Outgoing
    # --------
    def sends_updated(self):
        self.update_hierarchy()
        # self.update(PyroDevice.DEVICE_UPDATED, {
        #     "track": self.track.name,
        #     "device": self.handle().name})

    # ---------
    # Utilities
    # ---------
    def update_hierarchy(self):   
        Log.info("Send list changed")
        PyroWrapper.update_hierarchy(self, PyroSend, self.handle().sends)