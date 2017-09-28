from LiveWrapper import *
from ..Utils import Utils
from ..Logger import Log
import showtime
from showtime import Showtime as ZST
from showtime import ZstURI, ZstPlugDataEventCallback


class LiveDeviceParameter(LiveWrapper):
    def create_handle_id(self):
        return "%sp%s" % (self.parent().id(), self.handleindex)

    def create_listeners(self):
        LiveWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_value_listener(self.value_updated)

    def create_plugs(self):
        try:
            self.value_plug_out = self.create_output_plug("out", showtime.ZST_FLOAT)
            self.value_plug_in = self.create_input_plug("in", showtime.ZST_FLOAT)
        except Exception as e:
            Log.error("Failed to register plug. Exception was {0}".format(e))

    def destroy_listeners(self):
        LiveWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_value_listener(self.value_updated)
            except (RuntimeError, AttributeError):
                Log.warn("Couldn't remove deviceparameter listener")

    def destroy_plugs(self):
        LiveWrapper.destroy_plugs(self)
        self.remove_plug(self.value_plug_out)
        self.remove_plug(self.value_plug_in)
        self.value_plug_out = None
        self.value_plug_in = None
        self.input_callback = None

    def compute(self, plug):
        Log.info("LIVE: Plug received message")
        self.apply_param_value(plug.float_at(0))

    def apply_param_value(self, value):
        self.handle().value = Utils.clamp(self.handle().min, self.handle().max, float(value))
        Log.info("Val:%s on %s" % (self.handle().value, self.id()))

    def value_updated(self):
        Log.info("Sending on native plug: {0}".format(self.handle().value))
        self.value_plug_out.append_float(self.handle().value)
        self.value_plug_out.fire()
