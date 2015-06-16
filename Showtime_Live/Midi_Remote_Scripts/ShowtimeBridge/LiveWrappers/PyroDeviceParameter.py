from PyroWrapper import *

class PyroDeviceParameter(PyroWrapper):
    # Message types
    PARAM_UPDATED = "param_update"
    PARAM_SET_VALUE = "param_set_value"

    def __init__(self, parameterindex, handle, parent):
        PyroWrapper.__init__(self, handle, parent)
        self.parameterindex = parameterindex
        self.queued_value = None
        self.handle().add_value_listener(self.value_updated)

    @classmethod
    def register_methods(cls):
        PyroDeviceParameter.add_outgoing_method(PyroDeviceParameter.PARAM_UPDATED)
        PyroDeviceParameter.add_incoming_method(
            PyroDeviceParameter.PARAM_SET_VALUE, ["id", "value"],
            PyroDeviceParameter.set_value)

    '''Apply the queued wrapper value post-eventloop'''
    def apply_queued_event(self):
        if self.queued_value:
            self.handle().value = self.queued_value
            self.queued_value = None

    # Incoming
    # --------
    @staticmethod
    def set_value(args):
        instance = PyroDeviceParameter.findById(args["id"])
        instance.queued_value = float(args["value"])
        instance.flag_as_queued()

    # Outgoing
    # --------
    def value_updated(self):
        self.update(PyroDeviceParameter.PARAM_UPDATED, self.handle().value)
