import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "ext_libs"))

from Pyro.EventService.Clients import Subscriber
from LiveWrappers.PyroWrapper import PyroWrapper
from PyroShared import PyroPrefixes
from Logger import Log

# Event listener class for recieving/parsing messages from Live
class LiveSubscriber(Subscriber):

    def __init__(self, publisher):
        Subscriber.__init__(self)
        self.setThreading(False)

        self.publisher = publisher
        self.requestLock = True
        self.incomingSubscriptions = {}

    def add_incoming_action(self, action, cls, callback):
        self.incomingSubscriptions[PyroPrefixes.prefix_incoming(action)] = {"class":cls, "function":callback}
        self.subscribe(self.incomingSubscriptions.keys())

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
            Log.warn(str(requestCounter) + " loops to clear queue")

        # Apply all wrapper values that have been queued
        for cls in PyroWrapper.__subclasses__():
            cls.process_deferred_actions()

    def event(self, event):
        self.requestLock = True     # Lock the request loop
        Log.info("Received method " + event.subject[2:])
        Log.info("Args are:" + str(event.msg)) 
        self.incomingSubscriptions[event.subject]["function"](event.msg)
