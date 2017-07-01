from LiveWrapper import *
from ..Utils import Utils

from ..Logger import Log
import showtime


class LiveDeviceParameter(LiveWrapper):
    # Message types
    PARAM_UPDATED = "param_updated"
    PARAM_SET = "param_set"

    def create_handle_id(self):
        return "%sp%s" % (self.parent().id(), self.handleindex)

    # -------------------
    # Wrapper definitions
    # -------------------
    def create_listeners(self):
        LiveWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_value_listener(self.value_updated)

    def create_plugs(self):
        if not self.showtime_instrument:
            Log.warn("No showtime_instrument string set. Value is {0}".format(self.showtime_instrument))
            return

        uri_out = showtime.ZstURI.create("ableton_perf", str(self.showtime_instrument), "out", showtime.ZstURI.OUT_JACK)
        uri_in = showtime.ZstURI.create("ableton_perf", str(self.showtime_instrument), "in", showtime.ZstURI.IN_JACK)

        try:
            self.value_plug_out = showtime.Showtime_create_int_plug(uri_out)
            self.value_plug_in = showtime.Showtime_create_int_plug(uri_in)
            LiveWrapper.add_plug_uri(uri_out, self)
            LiveWrapper.add_plug_uri(uri_in, self)
        except Exception as e:
            Log.error("Failed to register plug. Exception was {0}".format(e))

    def destroy_listeners(self):
        LiveWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_value_listener(self.value_updated)
            except (RuntimeError, AttributeError):
                Log.warn("Couldn't remove deviceparameter listener")

            try:
                LiveWrapper.remove_plug_uri(self.value_plug_out.get_URI())
                LiveWrapper.remove_plug_uri(self.value_plug_in.get_URI())
            except:
                Log.error("Failed to remove plug uris")
            showtime.Showtime_destroy_plug(self.value_plug_out)
            showtime.Showtime_destroy_plug(self.value_plug_in)

    def handle_incoming_plug_event(self, event):
        Log.info("LIVE: Plug received message")
        if event.get_first() == self.value_plug_in.get_URI():
            self.handle().value = Utils.clamp(self.handle().min, self.handle().max, float(self.value_plug_in.get_value())/127.0)
            Log.info("Val:%s on %s" % (self.handle().value, self.id()))
        else:
            Log.warn("No registered input plug matches incoming plug event from {0}".format(event.get_first().to_char()))

    # --------
    # Incoming
    # --------
    def apply_param_value(self, value):
        self.handle().value = Utils.clamp(self.handle().min, self.handle().max, float(value))
        Log.info("Val:%s on %s" % (self.handle().value, self.id()))

    # --------
    # Outgoing
    # --------
    def value_updated(self):
        # self.update(LiveDeviceParameter.PARAM_UPDATED, self.handle().value)
        Log.info("Sending on native plug: {0}".format(self.handle().value))
        self.value_plug_out.fire(int(self.handle().value))
