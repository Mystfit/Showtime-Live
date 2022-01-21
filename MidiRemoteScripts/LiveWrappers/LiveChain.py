from ShowtimeLive.LiveWrappers.LiveWrapper import LiveWrapper
from ShowtimeLive.LiveWrappers import LiveDevice
from ShowtimeLive.Logger import Log


class LiveChain(LiveWrapper):
    def __init__(self, name, handle, handleindex):
        LiveWrapper.__init__(self, name, handle, handleindex)
        self.devices = ZST.ZstComponent("devices")
        showtime.client().register_entity(self.devices)
        
    def on_registered(self, entity):
        LiveWrapper.on_registered(self, entity)
        self.component.add_child(self.devices)

    @staticmethod
    def build_name(handle, handle_index):
        return handle.name

    def create_listeners(self):
        LiveWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_devices_listener(self.refresh_hierarchy)

    def destroy_listeners(self):
        LiveWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_devices_listener(self.refresh_hierarchy)
            except (RuntimeError, AttributeError):
                Log.warn("Couldn't remove device listener")

    def refresh_devices(self, postactivate=True):
        Log.info("{0} - Chain device list changed".format(self.component.URI().last().path()))
        LiveWrapper.update_hierarchy(self.devices, LiveDevice.LiveDevice, self.handle().devices, postactivate)

    def refresh_hierarchy(self, postactivate):
        self.refresh_devices(postactivate)
