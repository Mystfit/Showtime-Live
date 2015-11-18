import sys, os
from PyroShared import PyroPrefixes
from Logger import Log
from UDPEndpoint import UDPEndpoint, SimpleMessage

class LiveUDPEndpoint(UDPEndpoint):

    def __init__(self, localPort, remotePort, threading):
        self.requestLock = True
        self.incomingSubscriptions = {}
        UDPEndpoint.__init__(self, localPort, remotePort, threading)

    def add_incoming_action(self, action, cls, callback):
        self.incomingSubscriptions[PyroPrefixes.prefix_incoming(action)] = {"class":cls, "function":callback}

    def send_to_showtime(self, message, args, responding=False):
        if responding:
            pass
        return self.send_msg(SimpleMessage(PyroPrefixes.prefix_outgoing(message), args))

    def send_to_live(self, message, args):
        return self.send_msg(SimpleMessage(PyroPrefixes.prefix_incoming(message), args))

    def register_to_showtime(self, message, methodaccess, methodargs=None):
        return self.send_msg(SimpleMessage(PyroPrefixes.prefix_registration(message), {"args": methodargs, "methodaccess": methodaccess}))

    def handle_requests(self):
        requestCounter = 0

        # Loop through all messages in the socket till it's empty
        # If the lock is active, then the queue is not empty
        while self.requestLock:
            self.requestLock = False
            try:
                self.recv_msg()
            except Exception, e:
                print e
            requestCounter += 1
        self.requestLock = True
        if requestCounter > 10:
            Log.warn(str(requestCounter) + " loops to clear queue")

    def event(self, event):
        self.requestLock = True     # Lock the request loop
        Log.info("Received method " + event.subject[2:])
        Log.info("Args are:" + str(event.msg)) 
        self.incomingSubscriptions[event.subject]["function"](event.msg)