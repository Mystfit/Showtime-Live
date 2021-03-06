import Live
from _Framework.EncoderElement import *
from _Framework.InputControlElement import InputControlElement, MIDI_SYSEX_TYPE
from _Framework.Util import *


class LoopingEncoderElement(EncoderElement):

    def __init__(self, channel, identifier, parameter=None, parametertuple=None):
        EncoderElement.__init__(self, msg_type=MIDI_CC_TYPE, channel=channel, identifier=identifier, map_mode=Live.MidiMap.MapMode.absolute)
        self._report_input = True
        self._report_output = True
        self.log_message = None
        self.publisher = None

    def set_publisher(self, publisher):
        self.publisher = publisher

    def set_debugger(self, logger):
        self.log_message = logger

    def message_map_mode(self):
        return Live.MidiMap.MapMode.absolute

    def script_wants_forwarding(self):
        return True
