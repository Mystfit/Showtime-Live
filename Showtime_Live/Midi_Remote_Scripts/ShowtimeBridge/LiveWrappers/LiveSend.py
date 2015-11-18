from LiveWrapper import *


class LiveSend(LiveWrapper):
    # Message types
    SEND_UPDATED = "send_updated"
    SEND_SET = "send_set"    

    def create_handle_id(self):
        return "%ss%s" % (self.parent().id(), self.handleindex)

    # -------------------
    # Wrapper definitions
    # -------------------
    def create_listeners(self):
        LiveWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_value_listener(self.send_updated)

    def destroy_listeners(self):
        LiveWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_value_listener(self.send_updated)
            except RuntimeError:
                Log.warn("Couldn't remove send listener")

    @classmethod
    def register_methods(cls):
        LiveSend.add_outgoing_method(LiveSend.SEND_UPDATED)
        LiveSend.add_incoming_method(
            LiveSend.SEND_SET,
            ["id", "value"],
            LiveSend.send_set
        )

    # --------
    # Incoming
    # --------
    @staticmethod
    def send_set(args):
        instance = LiveSend.find_wrapper_by_id(args["id"])
        instance.defer_action(instance.apply_send_value, args["value"])

    def apply_param_value(self, value):
        Log.info("Val:" + value + " on " + str(self))
        self.handle().value = float(value)

    # --------
    # Outgoing
    # --------
    def send_updated(self):
        self.update(LiveSend.SEND_UPDATED, self.handle().value)
