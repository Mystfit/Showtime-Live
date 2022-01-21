from ShowtimeLive.LiveWrappers.LiveWrapper import LiveWrapper
from ShowtimeLive.LiveWrappers.LiveDeviceParameter import LiveDeviceParameter
from ShowtimeLive.Logger import Log
from ShowtimeLive.showtimeAPI import API as ZST
import ShowtimeLive.showtimeAPI as showtime

class LiveDevice(LiveWrapper):

    def __init__(self, name, handle, handleindex):
        LiveWrapper.__init__(self, name, handle, handleindex)
        self.chains = None
        if self.handle().can_have_chains:
            self.chains = ZST.ZstComponent("chains")
            showtime.client().register_entity(self.chains)

        
    def on_registered(self, entity):
        LiveWrapper.on_registered(self, entity)
        if self.handle().can_have_chains:
            self.component.add_child(self.chains)

    @staticmethod
    def build_name(handle, handle_index):
        return handle.name

    def create_listeners(self):
        LiveWrapper.create_listeners(self)
        if self.handle():
            Log.info("Registering parameter listeners")
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
        Log.info("{0} - Parameter list changed".format(self.component.URI().last().path()))
        LiveWrapper.update_hierarchy(self.component, LiveDeviceParameter, self.handle().parameters, postactivate)

    def refresh_chains(self, postactivate=True):
        Log.info("{0} - Chain list changed".format(self.component.URI().last().path()))
        LiveWrapper.update_hierarchy(self.chains, LiveChain, self.handle().chains, postactivate)

    def refresh_hierarchy(self, postactivate):
        self.refresh_parameters(postactivate)
        if self.handle().can_have_chains:
            if hasattr(self.handle(), "chains"):
                self.refresh_chains(postactivate)


# Imported last to avoid circular import issues
from ShowtimeLive.LiveWrappers.LiveChain import LiveChain
