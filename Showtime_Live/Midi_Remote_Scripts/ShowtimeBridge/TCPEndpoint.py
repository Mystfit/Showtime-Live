import socket

from Logger import Log
from NetworkEndpoint import NetworkEndpoint, NetworkPrefixes, NetworkErrors, SimpleMessage


class TCPEndpoint(NetworkEndpoint):
    """Network endpoint using TCP"""
    def __init__(self, localport, remoteport, threaded=True, isserversocket=True, existingsocket=None):
        self.serverSocket = isserversocket
        self.hangup = False
        self.clientHandshakeCallbacks = set()
        self.handshakeAckCallbacks = set()
        if existingsocket:
            self.socket = existingsocket
        NetworkEndpoint.__init__(self, localport, remoteport, threaded)

    def close(self):
        self.hangup = True
        NetworkEndpoint.close(self)

    def create_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(5)

        if self.serverSocket:
            self.socket.bind(self.localAddr)
            self.socket.listen(2)

        if not self.threaded:
            self.socket.setblocking(0)
        else:
            self.socket.setblocking(1)

    def connect(self):
        self.create_socket()
        status = 0
        retries = 5
        while retries > 0:
            try:
                status = self.socket.connect(self.remoteAddr)
            except socket.error, e:
                if e[0] == NetworkErrors.EISCONN:
                    Log.network("...TCP connected!")
                    self.connectionStatus = NetworkEndpoint.PIPE_CONNECTED
                    break
                elif e[0] == NetworkErrors.EAGAIN:
                    Log.network("TCP connecting...")
                    retries -= 1
                elif e[0] == socket.timeout:
                    Log.error("Timed out")
                    self.connectionStatus = NetworkEndpoint.PIPE_DISCONNECTED
                else:
                    Log.error("Connection failed!")
                    Log.error("Reason: " + str(e))
                    self.connectionStatus = NetworkEndpoint.PIPE_DISCONNECTED
                    break

        if status == 0:
            self.connectionStatus = NetworkEndpoint.PIPE_CONNECTED
        else:
            Log.error("Connection failed with error %s" % status)
        
        return self.connectionStatus

    def event(self, event):
        if event.subject == NetworkPrefixes.HANDSHAKE:
            Log.network("TCP handshake received. Socket is %s" % self.socket)
            if self.connectionStatus == NetworkEndpoint.PIPE_CONNECTED:
                self.connectionStatus = NetworkEndpoint.HANDSHAKING
                for callback in self.clientHandshakeCallbacks:
                    callback()
            return
        elif event.subject == NetworkPrefixes.HANDSHAKE_ACK:
            Log.network("TCP handshake ACK received")
            self.connectionStatus = NetworkEndpoint.HANDSHAKE_COMPLETE
            for callback in self.handshakeAckCallbacks:
                callback()
            return
        NetworkEndpoint.event(self, event)

    def send_handshake(self):
        Log.network("Sending TCP handshake")
        self.send_msg(SimpleMessage(NetworkPrefixes.HANDSHAKE, None))
        self.connectionStatus = NetworkEndpoint.HANDSHAKING

    def send_handshake_ack(self):
        Log.network("Sending TCP handshake ACK on %s" % self.socket)
        self.send_msg(SimpleMessage(NetworkPrefixes.HANDSHAKE_ACK, None))

    # Callback management
    # -------------------
    def add_client_handshake_callback(self, callback):
        self.clientHandshakeCallbacks.add(callback)

    def remove_client_handshake_callback(self, callback):
        self.clientHandshakeCallbacks.remove(callback)

    def add_handshake_ack_callback(self, callback):
        self.handshakeAckCallbacks.add(callback)

    def remove_handshake_ack_callback(self, callback):
        self.handshakeAckCallbacks.remove(callback)


