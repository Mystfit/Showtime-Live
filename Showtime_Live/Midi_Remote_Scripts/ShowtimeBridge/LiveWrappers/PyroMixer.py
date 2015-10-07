from PyroWrapper import *
from PyroDeviceParameter import PyroDeviceParameter
from PyroSend import PyroSend
from ..Utils import Utils


class PyroMixer(PyroWrapper):
    # Message types
    MIXER_SENDS_UPDATED = "mixer_sends_updated"
    # MIXER_VOLUME_SET = "mixer_volume_set"
    # MIXER_VOLUME_UPDATED = "mixer_volume_updated"


    def create_handle_id(self):
        return "%sm" % self.parent().id()
    
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
        PyroWrapper.add_outgoing_method(PyroMixer.MIXER_SENDS_UPDATED)
        # PyroWrapper.add_incoming_method(
        #     PyroMixer.MIXER_VOLUME_SET,
        #     ["id", "value"],
        #     PyroMixer.queue_volume
        # )


    # --------
    # Outgoing
    # --------
    def sends_updated(self):
        self.update_hierarchy()

    # --------
    # Incoming
    # --------
    # @staticmethod
    # def queue_volume(args):
    #     Log.info("About to find mixer")
    #     instance = PyroMixer.find_wrapper_by_id(args["id"])
    #     Log.info("Mixer is %s" % instance)
    #     if instance:
    #         instance.defer_action(instance.apply_volume, args["value"])
    #     else:
    #         Log.warn("Could not find Mixer for track %s " % instance.parent().name)

    # def apply_volume(self, value):
    #     self.handle().volume.value = Utils.clamp(self.handle().volume.min, self.handle().volume.max, float(value))
    #     Log.info("Val:%s on %s" % (self.handle().volume.value, self.id()))


    # ---------
    # Utilities
    # ---------
    def update_hierarchy(self):   
        Log.info("Send list changed")
        PyroWrapper.update_hierarchy(self, PyroSend, self.handle().sends)
        PyroDeviceParameter.add_instance(PyroDeviceParameter(self.handle().volume, 0, self))
        PyroDeviceParameter.add_instance(PyroDeviceParameter(self.handle().panning, 0, self))
