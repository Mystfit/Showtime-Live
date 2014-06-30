import Live
from _Framework.ButtonElement import *
from _Framework.InputControlElement import *
from _Framework.SysexValueControl import *

from .. import LiveUtils
from _Framework.Util import *


class PyroButtonElement(ButtonElement):

    # def __init__(self, message_prefix = None, value_enquiry = None, default_value = None, *a, **k):
    #     super(SysexValueControl, self).__init__(message_prefix, value_enquiry, default_value, *a, **k)
    #     self.pyroRemote = None

    def set_remote(self, pyroconnector):
        self.connector = pyroconnector

    def receive_value(self, value):
        ButtonElement.receive_value(self, value)
        self.log_message("Recieved message: " + str(value))

    def send_value(self, value):
        ButtonElement.send_value(self, value)
        self.connector.publish_clip_launch(self.name, value)

    # def _verify_value(self, value):
    #     upper_bound = 16384
    #     if not in_range(value, 0, upper_bound):
    #         raise AssertionError

    def turn_on(self):
        self.send_value(ON_VALUE)

    def turn_off(self):
        self.send_value(OFF_VALUE)

    def remote_turn_on(self):
        self.receive_value(ON_VALUE)

    def remote_turn_off(self):
        self.receive_value(OFF_VALUE)
