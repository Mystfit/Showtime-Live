from LiveWrapper import *
from ..Utils import Utils


class LiveDeviceParameter(LiveWrapper):
    # Message types
    PARAM_UPDATED = "param_updated"
    PARAM_SET = "param_set"

    def create_handle_id(self):
        return "%sp%s" % (self.parent().id(), self.handleindex)

    # -------------------
    # Wrapper definitions
    # -------------------
    def create_listeners(self):
        LiveWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_value_listener(self.value_updated)

    def destroy_listeners(self):
        LiveWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_value_listener(self.value_updated)
            except RuntimeError:
                Log.warn("Couldn't remove deviceparameter listener")

    @classmethod
    def register_methods(cls):
        LiveDeviceParameter.add_outgoing_method(LiveDeviceParameter.PARAM_UPDATED)
        LiveDeviceParameter.add_incoming_method(
            LiveDeviceParameter.PARAM_SET, ["id", "value"],
            LiveDeviceParameter.queue_param_value)

    def to_object(self):    
        params = {
            "value": self.handle().value,
            "min": self.handle().min,
            "max": self.handle().max,
        }   
        return LiveWrapper.to_object(self, params)
        

    # --------
    # Incoming
    # --------
    @staticmethod
    def queue_param_value(args):
        instance = LiveDeviceParameter.find_wrapper_by_id(args["id"])
        if instance:
            instance.defer_action(instance.apply_param_value, args["value"])
        else:
            Log.warn("Could not find DeviceParameter %s " % instance.name)

    def apply_param_value(self, value):
        self.handle().value = Utils.clamp(self.handle().min, self.handle().max, float(value))
        Log.info("Val:%s on %s" % (self.handle().value, self.id()))

    # --------
    # Outgoing
    # --------
    def value_updated(self):
        self.update(LiveDeviceParameter.PARAM_UPDATED, self.handle().value)
