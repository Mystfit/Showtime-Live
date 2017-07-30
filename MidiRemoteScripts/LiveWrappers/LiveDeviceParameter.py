from LiveWrapper import *
from ..Utils import Utils
from ..Logger import Log
import showtime
from showtime import Showtime as ZST
from showtime import ZstURI, ZstPlugDataEventCallback


class PlugCallback(ZstPlugDataEventCallback):
    def set_wrapper(self, wrapper):
        self.wrapper = wrapper

    def run(self, plug):
        Log.info("LIVE: Plug received message")
        self.wrapper.apply_param_value(plug.value().float_at(0))


class LiveDeviceParameter(LiveWrapper):
    def create_handle_id(self):
        return "%sp%s" % (self.parent().id(), self.handleindex)

    def create_listeners(self):
        LiveWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_value_listener(self.value_updated)

    def create_plugs(self):
        if not self.showtime_instrument:
            Log.warn("No showtime_instrument string set. Value is {0}".format(self.showtime_instrument))
            return

        uri_out = ZstURI("ableton_perf", str(self.showtime_instrument), "out")
        uri_in = ZstURI("ableton_perf", str(self.showtime_instrument), "in")

        try:
            self.value_plug_out = ZST.create_output_plug(uri_out, showtime.ZST_FLOAT)
            self.value_plug_in = ZST.create_input_plug(uri_in, showtime.ZST_FLOAT)
        except Exception as e:
            Log.error("Failed to register plug. Exception was {0}".format(e))

        self.input_callback = PlugCallback()
        self.input_callback.set_wrapper(self)
        self.value_plug_in.input_events().attach_event_callback(self.input_callback)

    def destroy_listeners(self):
        LiveWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_value_listener(self.value_updated)
            except (RuntimeError, AttributeError):
                Log.warn("Couldn't remove deviceparameter listener")

    def destroy_plugs(self):
        LiveWrapper.destroy_plugs(self)
        showtime.Showtime_destroy_plug(self.value_plug_out)
        showtime.Showtime_destroy_plug(self.value_plug_in)
        self.input_callback = None

    def apply_param_value(self, value):
        self.handle().value = Utils.clamp(self.handle().min, self.handle().max, float(value))
        Log.info("Val:%s on %s" % (self.handle().value, self.id()))

    def value_updated(self):
        Log.info("Sending on native plug: {0}".format(self.handle().value))
        self.value_plug_out.value().append_float(self.handle().value)
        self.value_plug_out.fire()
        self.value_plug_out.value().clear()
