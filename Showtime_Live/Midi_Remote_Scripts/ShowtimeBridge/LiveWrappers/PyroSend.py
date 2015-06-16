from PyroWrapper import *

class PyroSend(PyroWrapper):
    # Message types
    SEND_UPDATED = "send_updated"
    SEND_SET = "send_set"    

    def __init__(self, sendindex, handle, parent):
        PyroWrapper.__init__(self, handle, parent)
        self.sendindex = sendindex
        self.handle().add_value_listener(self.send_updated)

    @classmethod
    def register_methods(cls):
        PyroSend.add_outgoing_method(PyroSend.SEND_UPDATED)
        PyroSend.add_incoming_method(PyroSend.SEND_SET, ["id", "value"], PyroSend.send_set)

    # def get_send(self):
    #     return getTrack(self.trackindex).mixer_device.sends[self.sendindex]

    @staticmethod
    def send_set(args):
        PyroSend.findById(args["id"]).handle().value = float(args["value"])

    def send_updated(self):
        self.update(PyroSend.SEND_UPDATED, self.handle().value)
