import sys, os, select, Queue, socket
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
        self.tcpEndpoint = TCPEndpoint(6004, 6003, False, False)
        self.udpEndpoint.add_event_callback(self.event_received)
        self.tcpEndpoint.add_event_callback(self.event_received)
        self.tcpEndpoint.add_handshake_callback(self.handshake_complete)
        self.udpEndpoint.add_ready_callback(self.endpoint_ready)
        # self.tcpEndpoint.add_ready_callback(self.endpoint_ready)
        self.udpEndpoint.add_closing_callback(self.heartbeat_lost)
        self.inputSockets = {self.tcpEndpoint.socket: self.tcpEndpoint, self.udpEndpoint.socket: self.udpEndpoint}
        self.outputSockets = {}

    def close(self):
        self.udpEndpoint.close()
        self.tcpEndpoint.close()

    def endpoint_ready(self, endpoint):
        self.outputSockets[endpoint.socket] = endpoint

    def handshake_complete(self):
        self.sync_actions()

    def sync_actions(self):
        # Register methods to the showtimebridge server
        wrapperClasses = LiveWrapper.__subclasses__()
        wrapperClasses.append(LiveWrapper)
        for cls in wrapperClasses:  
            cls.register_methods()
        for action in LiveWrapper.incoming_methods().values():
            Log.info("Adding %s to incoming callbacks" % action.methodName)
            self.add_incoming_action(action.methodName, cls, action.callback)
            self.register_to_showtime(action.methodName, action.methodAccess, action.methodArgs)
        for action in LiveWrapper.outgoing_methods().values():
            Log.info("Adding %s to outgoing callbacks" % action.methodName)
            self.register_to_showtime(action.methodName, action.methodAccess)

    def add_incoming_action(self, action, cls, callback):
        self.incomingActions[NetworkPrefixes.prefix_incoming(action)] = {"class":cls, "function":callback}

    def send_to_showtime(self, message, args, responding=False):
        ret = None
        if responding:
            ret = self.tcpEndpoint.send_msg(SimpleMessage(
                NetworkPrefixes.prefix_outgoing(message), args))
        else:
            ret = self.udpEndpoint.send_msg(SimpleMessage(
                NetworkPrefixes.prefix_outgoing(message), args), True)
        return ret

    def register_to_showtime(self, message, methodaccess, methodargs=None):
        return self.tcpEndpoint.send_msg(SimpleMessage(
            NetworkPrefixes.prefix_registration(message),
            {"args": methodargs, "methodaccess": methodaccess}))

    def heartbeat_lost(self):
        self.tcpEndpoint.hangup = False

    def poll(self):
        self.ensure_server_available()

        # Loop through all messages in the socket till it's empty
        # If the lock is active, then the queue is not empty
        requestCounter = 0
        while self.requestLock:
            self.requestLock = False
            badSockets = []
            
            try:
                inputready,outputready,exceptready = select.select(
                    self.inputSockets.keys(),
                    self.outputSockets.keys(),
                    badSockets, 0)
            except socket.error, e:
                if e[0] == 9:
                    Log.error("Bad file descriptor!")
                    Log.debug(self.inputSockets.keys())
                    Log.debug(self.outputSockets.keys())
            for s in inputready:
                endpoint = self.inputSockets[s]
                try:
                    endpoint.recv_msg()
                except RuntimeError:
                    try:
                        endpoint.close()
                        del self.inputSockets[endpoint.socket]
                        del self.outputSockets[self.tcpEndpoint.socket]
                    except KeyError:
                        Log.warn("Socket missing. In input hangup")
                    continue
            for s in outputready:
                try:
                    endpoint = self.outputSockets[s]
                except KeyError:
                    Log.warn("Socket missing. In output hangup")
                try:
                    while 1:
                        msg = endpoint.outgoingMailbox.get_nowait()
                        endpoint.send(msg)
                except Queue.Empty:
                    pass
                    ## Remove output socket from select once it's done sending 
                    # del self.outputSockets[endpoint.socket]
            

            requestCounter += 1
        self.requestLock = True
        if requestCounter > 10:
            Log.warn(str(requestCounter) + " loops to clear queue")

        
    def ensure_server_available(self):
        udpActive = self.udpEndpoint.check_heartbeat()
        if udpActive and not self.tcpEndpoint.peerConnected and not self.tcpEndpoint.hangup:
            Log.warn("Heartbeat found! Reconnecting TCP to " + str(self.tcpEndpoint.remoteAddr))
            if self.tcpEndpoint.connect():
                Log.info("TCP connection established. Waiting for handshake")
            else:
                Log.error("TCP not up yet!")

        if not udpActive and self.tcpEndpoint.peerConnected:
            Log.warn("Heartbeat lost")
            self.tcpEndpoint.close()

    def event_received(self, event):
        self.requestLock = True     # Lock the request loop
        Log.info("Received method " + event.subject[2:])
        Log.info("Args are:" + str(event.msg))
        try:
            self.incomingActions[event.subject]["function"](event.msg)
        except KeyError:
            Log.error("Nothing registered for incoming action " + event.subject)
