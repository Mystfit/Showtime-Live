import Live
from _Framework.EncoderElement import *
from _Framework.InputControlElement import InputControlElement, MIDI_SYSEX_TYPE
from _Framework.Util import *
from .. LiveWrappers import PyroDeviceParameter
import Pyro.errors


class PyroEncoderElement(EncoderElement):

    def __init__(self, channel, identifier, parameter, parametertuple):
        EncoderElement.__init__(self, msg_type=MIDI_CC_TYPE, channel=channel, identifier=identifier, map_mode=Live.MidiMap.MapMode.absolute)
        self.trackindex = parametertuple[0]
        self.deviceindex = parametertuple[1]
        self.parameterindex = parametertuple[2]
        self._report_input = True
        self._report_output = True
        self.connect(parameter)

    def set_publisher(self, publisher):
        self.publisher = publisher

    def set_debugger(self, logger):
        self.log_message = logger

    def message_map_mode(self):
        return Live.MidiMap.MapMode.absolute

    def script_wants_forwarding(self):
        return True

    def connect(self, parameter):
        if parameter:
            InputControlElement.connect_to(self, parameter)
            if self.mapped_parameter() is not None:
                try:
                    self.mapped_parameter().remove_value_listener(self.value_updated)
                except:
                    pass
            #self.mapped_parameter().add_value_listener(self.value_updated)

    def send_value(self, value):
        #EncoderElement.send_value(self, value)
        try:
            self.publisher.publish(PyroDeviceParameter.VALUE_UPDATED, {
                "trackindex": self.trackindex,
                "deviceindex": self.deviceindex,
                "parameterindex": self.parameterindex,
                "value": value})
        except Pyro.errors.ConnectionClosedError:
            print "Lost connection to event service"

    def value_updated(self):
        if self.mapped_parameter():
            self.send_value(self.mapped_parameter().value)
