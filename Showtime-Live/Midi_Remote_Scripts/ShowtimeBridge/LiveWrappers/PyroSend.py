from PyroWrappers import *


class PyroSendActions:
    pass


class PyroSend(PyroWrapper):

    def __init__(self, sendindex, publisher):
        PyroWrapper.__init__(self, publisher=publisher)
        self.sendindex = sendindex
        self.publisher = publisher
        self.devices = []
        self.ref_wrapper = self.get_send

    def get_send(self):
        return getSong().return_tracks[self.sendindex]
