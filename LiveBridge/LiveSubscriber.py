from Pyro.EventService.Clients import Subscriber
from LiveWrappers import *

from .. import PyroShared


# Event listener class for recieving/parsing messages from Live
class LiveSubscriber(Subscriber):

    def __init__(self, publisher, logger):
        Subscriber.__init__(self)
        self.log_message = logger
        self.setThreading(False)

        self.publisher = publisher
        self.requestLock = True
        self.songWrapper = None
        self.incomingActions = {}
        self.incomingSubscriptions = []

    def set_song(self, song):
        self.songWrapper = song

    def add_incoming_action(self, key, callback):
        self.incomingActions[key] = callback
        self.incomingSubscriptions.append(PyroShared.INCOMING_PREFIX + key)
        self.subscribe(self.incomingSubscriptions)

    def handle_requests(self):
        requestCounter = 0

        # Loop through all messages in the Pyro queue till it's empty
        # If the lock is active, then the queue is not empty
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

        if self.songWrapper:
            self.songWrapper.process_value_changed_messages()

    def event(self, event):
        self.requestLock = True     # Lock the request loop
        subject = event.subject[len(PyroShared.INCOMING_PREFIX):]
        self.log_message("Received method " + subject)

        if subject in self.incomingActions:
            self.log_message("Matched method " + subject + " with " + str(self.incomingActions[subject]))
            self.incomingActions[subject](event.msg)
        else:
            self.log_message("Incoming method not registered!")
