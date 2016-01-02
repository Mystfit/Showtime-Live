import Queue
import select
import socket

from LiveWrappers.LiveWrapper import LiveWrapper
from LiveWrappers.LiveSong import LiveSong
from Logger import Log
from NetworkEndpoint import SimpleMessage, NetworkPrefixes, NetworkErrors, NetworkEndpoint, ReadError
from TCPEndpoint import TCPEndpoint
from UDPEndpoint import UDPEndpoint


class LiveNetworkEndpoint:
    def __init__(self):
        self.getsong = None
        self.requestLock = True
        self.incomingActions = {}
        self.udpEndpoint = UDPEndpoint(6002, 6001, False)
        self.tcpEndpoint = TCPEndpoint(6004, 6003, False, False)
        self.udpEndpoint.add_event_callback(self.event_received)
        self.tcpEndpoint.add_event_callback(self.event_received)
        self.tcpEndpoint.add_handshake_ack_callback(self.handshake_complete)
        self.udpEndpoint.add_ready_callback(self.endpoint_ready)
        self.udpEndpoint.add_closing_callback(self.heartbeat_lost)
        self.inputSockets = {self.udpEndpoint.socket: self.udpEndpoint}
        self.outputSockets = {}

    def set_song_root_accessor(self, songgetter):
        self.getsong = songgetter

    def close(self):
        self.udpEndpoint.close()
        self.tcpEndpoint.close()

    def sync_actions(self):
        # Register methods to the showtimebridge server
        wrapperclasses = LiveWrapper.__subclasses__()
        wrapperclasses.append(LiveWrapper)
        for cls in wrapperclasses:
            cls.register_methods()
        for action in LiveWrapper.incoming_methods().values():
            Log.network("Adding %s to incoming callbacks" % action.methodName)
            self.add_incoming_action(action.methodName, action.callback)
            self.register_to_showtime(action.methodName, action.methodAccess, action.methodArgs)
        for action in LiveWrapper.outgoing_methods().values():
            Log.network("Adding %s to outgoing callbacks" % action.methodName)
            self.register_to_showtime(action.methodName, action.methodAccess)

    def add_incoming_action(self, action, callback):
        self.incomingActions[NetworkPrefixes.prefix_incoming(action)] = callback

    def send_to_showtime(self, message, args, responding=False):
        ret = None
        if responding:
            if self.tcpEndpoint.connectionStatus == NetworkEndpoint.HANDSHAKE_COMPLETE:
                msg = str(SimpleMessage(NetworkPrefixes.prefix_outgoing(message), args))
                ret = self.tcpEndpoint.send_msg(msg)
        else:
            msg = SimpleMessage(NetworkPrefixes.prefix_outgoing(message), args)
            ret = self.udpEndpoint.send_msg(msg, True)
        return ret

    def register_to_showtime(self, message, methodaccess, methodargs=None):
        return self.tcpEndpoint.send_msg(SimpleMessage(
                NetworkPrefixes.prefix_registration(message),
                {"args": methodargs, "methodaccess": methodaccess}), True)

    def poll(self):
        self.ensure_server_available()

        # Loop through all messages in the socket till it's empty
        # If the lock is active, then the queue is not empty
        requestcounter = 0
        while self.requestLock:
            self.requestLock = False
            badsockets = []
            inputready = None
            outputready = None

            try:
                inputready, outputready, exceptready = select.select(
                        self.inputSockets.keys(),
                        self.outputSockets.keys(),
                        badsockets, 0)
            except socket.error, e:
                if e[0] == NetworkErrors.EBADF:
                    Log.error("Bad file descriptor! Probably a dead socket passed to select")
                    Log.debug(self.inputSockets.keys())
                    Log.debug(self.outputSockets.keys())

            if badsockets:
                Log.error("Bad sockets: %s" % badsockets)

            if inputready:
                for s in inputready:
                    endpoint = self.inputSockets[s]
                    try:
                        endpoint.recv_msg()
                    except (ReadError, RuntimeError), e:
                        Log.error("Socket receive error! Closing %s. Reason: %s" % (endpoint, e))
                        endpoint.close()
                        try:
                            del self.inputSockets[endpoint.socket]
                            del self.outputSockets[endpoint.socket]
                            try:
                                outputready.remove(endpoint.socket)
                            except ValueError:
                                pass
                        except KeyError:
                            Log.network("Socket missing. In input hangup")
                        continue

            if outputready:
                for s in outputready:
                    endpoint = self.outputSockets[s]
                    try:
                        while 1:
                            msg = endpoint.outgoingMailbox.get_nowait()
                            endpoint.send(msg)
                    except Queue.Empty:
                        pass
                        # Remove output socket from select once it's done sending
                        # del self.outputSockets[endpoint.socket]

            requestcounter += 1
        self.requestLock = True
        if requestcounter > 10:
            Log.warn(str(requestcounter) + " loops to clear queue")

    def ensure_server_available(self):
        udpactive = self.udpEndpoint.check_heartbeat()
        if udpactive and self.tcpEndpoint.connectionStatus is NetworkEndpoint.PIPE_DISCONNECTED and not \
                self.tcpEndpoint.hangup:
            Log.network("Heartbeat found! Reconnecting TCP to " + str(self.tcpEndpoint.remoteAddr))

            if self.tcpEndpoint.connect():
                self.inputSockets[self.tcpEndpoint.socket] = self.tcpEndpoint
                self.outputSockets[self.tcpEndpoint.socket] = self.tcpEndpoint
                Log.network("TCP connection established. Socket is %s" % self.tcpEndpoint.socket)
            else:
                Log.warn("TCP not up yet!")

        if not udpactive and self.tcpEndpoint.connectionStatus >= NetworkEndpoint.PIPE_CONNECTED:
            Log.network("Heartbeat lost. Closing TCP")
            self.tcpEndpoint.close()
            try:
                del self.inputSockets[self.tcpEndpoint.socket]
                del self.outputSockets[self.tcpEndpoint.socket]
            except KeyError:
                Log.error("TCP already removed from pollable sockets")

        if self.tcpEndpoint.connectionStatus == NetworkEndpoint.PIPE_CONNECTED:
            self.tcpEndpoint.send_handshake()

    def event_received(self, event):
        self.requestLock = True  # Lock the request loop
        Log.info("Received method " + event.subject[2:])
        Log.info("Args are:" + str(event.msg))
        try:
            self.incomingActions[event.subject](event.msg)
        except KeyError:
            Log.error("Nothing registered for incoming action " + event.subject)

    # Socket Callbacks
    # ---------
    def endpoint_ready(self, endpoint):
        self.outputSockets[endpoint.socket] = endpoint

    def handshake_complete(self):
        Log.network("Handshake completed")
        self.sync_actions()

        # Add wrappers to Live objects
        LiveSong.add_instance(LiveSong(self.getsong()))

    def heartbeat_lost(self):
        self.tcpEndpoint.hangup = False
