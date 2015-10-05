from PyroWrapper import *
from ..Utils import Utils


class PyroDeviceParameter(PyroWrapper):
    # Message types
    PARAM_UPDATED = "param_update"
    PARAM_SET_VALUE = "param_set_value"

    def create_handle_id(self):
        return PyroDeviceParameter.format_parameter_id(self.parent().id(), self.handleindex)

    @staticmethod
    def format_parameter_id(parentId, parameterId):
        return str(parentId) + "p" + str(parameterId)

    # -------------------
    # Wrapper definitions
    # -------------------
    def create_listeners(self):
        PyroWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_value_listener(self.value_updated)

    def destroy_listeners(self):
        PyroWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_value_listener(self.value_updated)
            except RuntimeError:
                Log.warn("Couldn't remove deviceparameter listener")

    @classmethod
    def register_methods(cls):
        PyroDeviceParameter.add_outgoing_method(PyroDeviceParameter.PARAM_UPDATED)
        PyroDeviceParameter.add_incoming_method(
            PyroDeviceParameter.PARAM_SET_VALUE, ["id", "value"],
            PyroDeviceParameter.set_value)

    def to_object(self):
        params = {
            "value": self.handle().value,
            "min": self.handle().min,
            "max": self.handle().max,
        }
        return PyroWrapper.toObject(self, params)
        

    # --------
    # Incoming
    # --------
    @staticmethod
    def set_value(args):
        instance = PyroDeviceParameter.find_wrapper_by_id(args["id"])
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
        self.update(PyroDeviceParameter.PARAM_UPDATED, self.handle().value)
