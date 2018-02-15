from LiveWrapper import *
from LiveDeviceParameter import LiveDeviceParameter
import LiveChain


class LiveDevice(LiveWrapper):

    def __init__(self, name, handle, handleindex):
        LiveWrapper.__init__(self, name, handle, handleindex)
        self.parameters = ZstContainer("parameters")
        self.add_child(self.parameters)

        self.chains = None
        if self.handle().can_have_chains:
            self.chains = ZstContainer("chains")
            self.add_child(self.chains)

    @staticmethod
    def build_name(handle, handle_index):
        return handle.name

    def create_listeners(self):
        LiveWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_parameters_listener(self.refresh_parameters)

            if self.handle().can_have_chains:
                if hasattr(self.handle(), "chains"):
                    self.handle().add_chains_listener(self.refresh_chains)

    def destroy_listeners(self):
        LiveWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_parameters_listener(self.refresh_parameters)
                if self.handle().can_have_chains:
                    if hasattr("chains", self.handle().device):
                        self.handle().remove_chains_listener(self.refresh_chains)
            except (RuntimeError, AttributeError):
                Log.warn("Couldn't remove device listener")

    def create_plugs(self):
        pass


    # ---------
    # Hierarchy
    # ---------

    def refresh_parameters(self, postactivate=True):
        Log.info("{0} - Parameter list changed".format(self.URI().last().path()))
        LiveWrapper.update_hierarchy(self.parameters, LiveDeviceParameter, self.handle().parameters, postactivate)

    def refresh_chains(self, postactivate=True):
        Log.info("{0} - Chain list changed".format(self.URI().last().path()))
        LiveWrapper.update_hierarchy(self.chains, LiveChain.LiveChain, self.handle().chains, postactivate)

    def refresh_hierarchy(self, postactivate):
        self.refresh_parameters(postactivate)
        if self.handle().can_have_chains:
            if hasattr(self.handle(), "chains"):
                self.refresh_chains(postactivate)
