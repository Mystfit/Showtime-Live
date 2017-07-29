from LiveWrapper import *
from LiveDeviceParameter import LiveDeviceParameter
import LiveChain


class LiveDevice(LiveWrapper):
    def create_listeners(self):
        LiveWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_parameters_listener(self.update_parameters)

            if self.handle().can_have_chains:
                if hasattr("chains", self.handle()):
                    self.handle().add_chains_listener(self.update_chains)

    def destroy_listeners(self):
        LiveWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_parameters_listener(self.update_parameters)
                if self.handle().can_have_chains:
                    if hasattr("chains", self.handle().device):
                        self.handle().remove_chains_listener(self.update_chains)
            except (RuntimeError, AttributeError):
                Log.warn("Couldn't remove device listener")

    def create_plugs(self):
        pass

    def update_hierarchy(self):
        self.update_parameters()
        if self.handle().can_have_chains:
            if hasattr(self.handle(), "chains"):
                self.update_chains()

    def update_parameters(self):
        Log.info("%s - Parameter list changed" % self.id())
        # for parameter in self._children:
        #     LiveWrapper.destroy(parameter)
        LiveWrapper.update_hierarchy(self, LiveDeviceParameter, self.handle().parameters)

    def update_chains(self):
        Log.info("%s - Chain list changed" % self.id())
        LiveWrapper.update_hierarchy(self, LiveChain.LiveChain, self.handle().chains)
