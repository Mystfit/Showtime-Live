from PyroWrapper import *
from PyroDeviceParameter import PyroDeviceParameter


class PyroDevice(PyroWrapper):
    # Message types
    DEVICE_UPDATED = "device_parameters_updated"

    # @classmethod
    # def remove_child_wrappers(cls, livevector):
    #     pass
        # idlist = [PyroWrapper.get_id_from_name(handle.name) for handle in livevector]
        # for wrapper in cls.instances():
        #     if wrapper.id() not in idlist:
        #         Log.write("==============")
        #         Log.write(str(wrapper.id()) + " handle is missing in Live. Removing!")
        #         Log.write("Wrappers: ")
        #         for i in cls.instances():
        #             Log.write(i.id())
        #         Log.write("Live:")
        #         for i in idlist:
        #             Log.write(i)
        #         wrapper.destroy()
        #         Log.write("--------------")
        #         Log.write("")

        # super(PyroDevice, cls).remove_child_wrappers(livevector)

    
    # -------------------
    # Wrapper definitions
    # -------------------
    def create_listeners(self):
        PyroWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_parameters_listener(self.parameters_updated)

    def destroy_listeners(self):
        PyroWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_parameters_listener(self.parameters_updated)
            except RuntimeError:
                Log.write("Couldn't remove device listener")

    @classmethod
    def register_methods(cls):
        PyroWrapper.add_outgoing_method(PyroDevice.DEVICE_UPDATED)

    # --------
    # Outgoing
    # --------
    def parameters_updated(self):
        for parameter in self._children:
            parameter.destroy()

        self.update(PyroDevice.DEVICE_UPDATED, {
            "track": self.track.name,
            "device": self.handle().name})

    # ---------
    # Utilities
    # ---------
    def update_hierarchy(self):   
        Log.write("Parameter list changed")
        PyroWrapper.update_hierarchy(self, PyroDeviceParameter, self.handle().parameters)