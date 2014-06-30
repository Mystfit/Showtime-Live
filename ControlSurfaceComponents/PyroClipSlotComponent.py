class PyroClipSlotComponent():

    def __init__(self, name, clip_slot, remote, logger = None):

        self.name = name
        self.connector = remote
        self.clip_slot = clip_slot
        self.clip_slot.add_is_triggered_listener(self.status_changed)
        self.clip_slot.add_playing_status_listener(self.status_changed)

        self.debug = logger

    def status_changed(self):
        clipname = "empty"
        if self.clip_slot.clip != None:
            clipname = self.clip_slot.clip.name

        self.log_message("Firing slot")
        self.connector.publish_clip_launch(clipname)

    def log_message(self, msg):
        try:
            self.debug(msg)
        except:
            print(msg)