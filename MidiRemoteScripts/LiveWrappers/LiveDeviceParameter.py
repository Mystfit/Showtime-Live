from LiveWrapper import *
from ..Utils import Utils
from ..Logger import Log
from ..showtime import API as ZST


class LiveDeviceParameter(LiveWrapper):
    def __init__(self, name, handle, handleindex):
        self.value_plug_in = None
        self.value_plug_out = None
        LiveWrapper.__init__(self, name, handle, handleindex)

    @staticmethod
    def build_name(handle, handle_index):
        return handle.name

    def refresh_hierarchy(self, postactivate):
        pass

    def create_listeners(self):
        LiveWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_value_listener(self.value_updated)

    def create_plugs(self):
        self.value_plug_out = ZST.ZstOutputPlug("out", ZST.ZstValueType_FloatList)
        self.value_plug_in = ZST.ZstInputPlug("in", ZST.ZstValueType_FloatList)
        self.component.add_child(self.value_plug_out)
        self.component.add_child(self.value_plug_in)

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

    def compute(self, plug):
        Log.info("LIVE: Plug received message")
        self.apply_param_value(plug.float_at(0))

    def apply_param_value(self, value):
        self.handle().value = Utils.clamp(self.handle().min, self.handle().max, float(value))
        Log.info("Val:{0} Plug:{1}".format(self.handle().value, self.component.URI().path()))

    def value_updated(self):
        Log.info("Sending on {0}: {1}".format(self.component.URI().path(), self.handle().value))
        self.value_plug_out.append_float(self.handle().value)
        self.value_plug_out.fire()
