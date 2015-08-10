from PyroWrapper import *


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
                Log.write("Couldn't remove deviceparameter listener")

    @classmethod
    def register_methods(cls):
        PyroDeviceParameter.add_outgoing_method(PyroDeviceParameter.PARAM_UPDATED)
        PyroDeviceParameter.add_incoming_method(
            PyroDeviceParameter.PARAM_SET_VALUE, ["id", "value"],
            PyroDeviceParameter.set_value)

    def apply_queued_event(self):
        if self.queued_value:
            Log.write(str(self) + " has a queued event!")
            self.handle().value = self.queued_value
            self.queued_value = None

    # --------
    # Incoming
    # --------
    @staticmethod
    def set_value(args):
        instance = PyroDeviceParameter.findById(args["id"])
        # instance.queued_value = float(args["value"])
        # instance.flag_as_deferred()
        Log.write("Val:" + args["value"] + " on " + str(instance))

    # --------
    # Outgoing
    # --------
    def value_updated(self):
        self.update(PyroDeviceParameter.PARAM_UPDATED, self.handle().value)
