import sys, os
from Logger import Log
from NetworkEndpoint import SimpleMessage, NetworkPrefixes
from UDPEndpoint import UDPEndpoint
from TCPEndpoint import TCPEndpoint
from LiveWrappers.LiveWrapper import LiveWrapper


class LiveNetworkEndpoint():
    def __init__(self, ):
        self.requestLock = True
        self.incomingActions = {}
        
        self.udpEndpoint = UDPEndpoint(6002, 6001, False)        
        self.tcpEndpoint = TCPEndpoint(6004, 6003, False)
        self.udpEndpoint.add_event_callback(self.event)
        self.tcpEndpoint.add_event_callback(self.event)

    def close(self):
        self.udpEndpoint.close()
        self.tcpEndpoint.close()

    def sync_actions(self):
        # Register methods to the showtimebridge server
        wrapperClasses = LiveWrapper.__subclasses__()
        wrapperClasses.append(LiveWrapper)
        for cls in wrapperClasses:  
            cls.register_methods()
            for action in cls.incoming_methods().values():
                Log.info("Adding %s to incoming callbacks" % action.methodName)
                self.add_incoming_action(action.methodName, cls, action.callback)
                Log.info(self.register_to_showtime(action.methodName, action.methodAccess, action.methodArgs))

            for action in cls.outgoing_methods().values():
                Log.info("Adding %s to outgoing methods" % action.methodName)
                Log.info(self.register_to_showtime(action.methodName, action.methodAccess))

    def add_incoming_action(self, action, cls, callback):
        self.incomingActions[NetworkPrefixes.prefix_incoming(action)] = {"class":cls, "function":callback}

    def send_to_showtime(self, message, args, responding=False):
        endpoint = self.udpEndpoint
        if responding:
            endpoint = self.tcpEndpoint
        return endpoint.send_msg(SimpleMessage(
            NetworkPrefixes.prefix_outgoing(message), args))

    def register_to_showtime(self, message, methodaccess, methodargs=None):
        return self.tcpEndpoint.send_msg(SimpleMessage(
            NetworkPrefixes.prefix_registration(message),
            {"args": methodargs, "methodaccess": methodaccess}))

    def poll(self):
        requestCounter = 0

        # Loop through all messages in the socket till it's empty
        # If the lock is active, then the queue is not empty
        while self.requestLock:
            self.requestLock = False
            try:
                self.udpEndpoint.recv_msg()
                self.tcpEndpoint.recv_msg()
            except Exception, e:
                print e
            requestCounter += 1
        self.requestLock = True
        if requestCounter > 10:
            Log.warn(str(requestCounter) + " loops to clear queue")

        self.udpEndpoint.send_heartbeat()
        self.ensure_server_available()
        
    def ensure_server_available(self):
        udpActive = self.udpEndpoint.check_heartbeat()
        if udpActive and not self.tcpEndpoint.peerConnected:
            Log.warn("Heartbeat found! Reconnecting TCP to " + str(self.tcpEndpoint.remoteAddr))
            if self.tcpEndpoint.connect():
                Log.info("TCP connection successful")
                self.sync_actions()
            else:
                Log.error("TCP not up yet!")

        if not udpActive and self.tcpEndpoint.peerConnected:
            Log.warn("Heartbeat lost")
            self.tcpEndpoint.peerConnected = False

    def event(self, event):
        self.requestLock = True     # Lock the request loop
        Log.info("Received method " + event.subject[2:])
        Log.info("Args are:" + str(event.msg))
        try:
            self.incomingActions[event.subject]["function"](event.msg)
        except KeyError:
            Log.error("Nothing registered for incoming action " + event.subject)
