from Pyro.EventService.Clients import Subscriber

from LiveWrappers import *
from LiveUtils import *


# Event listener class for recieving/parsing messages from Live
class LiveSubscriber(Subscriber):

    def __init__(self, publisher, logger):
        Subscriber.__init__(self)
        self.log_message = logger
        self.setThreading(False)
        self.publisher = publisher

        self.valueChangedMessages = None
        self.requestLock = True
        self.parameters = None
        self.song = None

        subscribed = [
            PyroTrack.FIRE_CLIP,
            PyroDeviceParameter.SET_VALUE,
            PyroSong.GET_SONG_LAYOUT,
            PyroTrack.STOP_TRACK,
            PyroSendVolume.SET_SEND
        ]

        subscribed = [INCOMING_PREFIX + method for method in subscribed]
        self.log_message(subscribed)
        self.subscribe(subscribed)

    def set_parameter_list(self, parameterList):
        self.parameters = parameterList

    def set_song(self, song):
        self.song = song

    def handle_requests(self):
        requestCounter = 0

        # Loop through all messages in the Pyro queue till it's empty
        while self.requestLock:
            self.requestLock = False
            try:
                self.getDaemon().handleRequests(0)
            except Exception, e:
                print e
            requestCounter += 1
        self.requestLock = True
        if requestCounter > 10:
            self.log_message(str(requestCounter) + " loops to clear queue")

        if self.valueChangedMessages:
            self.process_value_changed_messages(self.valueChangedMessages)
            self.valueChangedMessages = None

    def process_value_changed_messages(self, queue):
        for parametertuple, value in queue.iteritems():
            try:
                if parametertuple in self.parameters:
                    self.parameters[parametertuple].get_reference().value = value
            except RuntimeError, e:
                self.log_message(e)

    def event(self, event):
        self.requestLock = True     # Lock the request loop
        subject = event.subject[len(INCOMING_PREFIX):]
        self.log_message("Received method " + subject)

        if hasattr(self, subject):
            getattr(self, subject)(event.msg)
        else:
            self.log_message("Incoming method not registered!")

    # ---------------------------
    # Incoming method controllers
    # ---------------------------
    def get_song_layout(self, args):
        self.log_message("Requesting song layout...")
        layout = self.song.get_song_layout(args)
        self.log_message(layout)

    def fire_clip(self, args):
        try:
            launchClip(int(args["trackindex"]), int(args["clipindex"]))
        except AttributeError:
            self.log_message("Clip not found! " + str(args["trackindex"]) + ", " + str(args["clipindex"]))

    def stop_track(self, args):
        self.log_message("Stopping track " + str(args["trackindex"]))
        stopTrack(int(args["trackindex"]))
        self.log_message("Stopped track")

    def set_send(self, args):
        self.log_message("Setting send value " + str(args["trackindex"]))
        trackSend(int(args["trackindex"]), int(args["sendindex"]), float(args["value"]))

    def set_value(self, args):
        key = (
            int(args["trackindex"]),
            int(args["deviceindex"]),
            int(args["parameterindex"]),
            int(args["category"]))

        # Rather than setting the parameter value immediately,
        # we combine similar value messages so only the most up to date
        # message gets applied when the clock triggers our update
        if not self.valueChangedMessages:
            self.valueChangedMessages = {}
        self.valueChangedMessages[key] = float(args["value"])
