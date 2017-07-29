from LiveWrapper import *
import LiveDevice

class LiveChain(LiveWrapper):
    def create_listeners(self):
        LiveWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_devices_listener(self.update_hierarchy)

    def destroy_listeners(self):
        LiveWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_devices_listener(self.update_hierarchy)
            except (RuntimeError, AttributeError):
                Log.warn("Couldn't remove device listener")

    def create_plugs(self):
        pass

    def update_hierarchy(self):
        Log.info("%s - Chain device list changed" % self.id())
        LiveWrapper.update_hierarchy(self, LiveDevice.LiveDevice, self.handle().devices)
