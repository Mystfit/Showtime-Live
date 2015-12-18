import socket
import threading
import time
import Queue
import struct

try:
    import json
except ImportError:
    import simplejson as json
from Logger import Log


class NetworkErrors:
    import platform
    import errno
    if platform.system() == "Windows":
        EAGAIN = errno.WSAEWOULDBLOCK
        ECONNRESET = errno.WSAECONNRESET
        EISCONN = errno.WSAEISCONN
        EBADF = errno.EBADF
    else:
        EAGAIN = errno.EAGAIN
        ECONNRESET = errno.ECONNRESET
        EISCONN = errno.EISCONN
        EBADF = errno.EBADF


class NetworkPrefixes:
    INCOMING = "I"
    OUTGOING = "O"
    RESPONDER = "L"
    REGISTRATION = "R"
    DELIMITER = "_"
    HEARTBEAT = "HB"
    HANDSHAKE = "HS"
    HANDSHAKE_ACK = "HSACK"

    @staticmethod
    def prefix_outgoing(name):
        return NetworkPrefixes.OUTGOING + NetworkPrefixes.prefix_name(name)

    @staticmethod
    def prefix_incoming(name):
        return NetworkPrefixes.INCOMING + NetworkPrefixes.prefix_name(name)

    @staticmethod
    def prefix_responder(name):
        return NetworkPrefixes.RESPONDER + NetworkPrefixes.prefix_name(name)
    
    @staticmethod
    def prefix_registration(name):
        return NetworkPrefixes.REGISTRATION + NetworkPrefixes.prefix_name(name)

    @staticmethod
    def prefix_name(name):
        return NetworkPrefixes.DELIMITER + name


class SimpleMessage:
    def __init__(self, subject, message):
        self.subject = subject
        self.msg = message if message else {}

    def __str__(self):
        return json.dumps([self.subject, self.msg])

    def __len__(self):
        return len(str(self))

    @staticmethod
    def parse(rawMsg):
        jsonmsg = json.loads(rawMsg)
        return SimpleMessage(jsonmsg[0], jsonmsg[1])


class NetworkEndpoint():
    MAX_MSG_SIZE = 1024

    # Connection statuses
    PIPE_DISCONNECTED = 0
    PIPE_CONNECTED = 1
    HANDSHAKING = 2
    HANDSHAKE_COMPLETE = 3

    def __init__(self, localPort, remotePort, threaded=True):
        self.threaded = threaded
        self.localAddr = ((''), localPort)
        self.remoteAddr = (("127.0.0.1"), remotePort)
        self.eventCallbacks = set()
        self.readyCallbacks = set()
        self.closingCallbacks = set()
        self.outgoingMailbox = Queue.Queue()
        self.connectionStatus = NetworkEndpoint.PIPE_DISCONNECTED
        if not hasattr(self, "socket"):
            self.create_socket()

    def create_socket(self):
        raise NotImplementedError

    def close(self):
        if self.socket:
            self.socket.close()
            self.connectionStatus = NetworkEndpoint.PIPE_DISCONNECTED

    @staticmethod
    def current_milli_time():
        return int(round(time.time() * 1000))

    # Send/Receive
    # ------------
    def recv_msg(self):
        self.recv()

    def recv(self):
        size = self._msgLength()
        data = self._read(size)
        frmt = "!%ds" % size
        msg = None
        if data:
            msg = struct.unpack(frmt,data)
        if msg:
            self.event(SimpleMessage.parse(msg[0]))

    def _msgLength(self):
        d = self._read(4)
        s = struct.unpack('!I', d)
        return s[0]

    def _read(self, size):
        data = ''
        while len(data) < size:
            retries = 10
            while retries > 0:
                try:
                    dataTmp = self.socket.recv(min(size-len(data), NetworkEndpoint.MAX_MSG_SIZE))
                    data += dataTmp
                    retries = 0
                    if dataTmp == '':
                        raise RuntimeError("Socket returned empty string. Connection broken")
                except socket.error, e:
                    if e[0] == NetworkErrors.EAGAIN:
                        Log.warn("Socket busy. Trying again")
                        retries -= 1
                    elif e[0] == NetworkErrors.ECONNRESET:
                        raise ReadError("Connection reset when reading or destination port closed.")
                    else:
                        raise RuntimeError("Socket connection broken. %s" % e)
        return data

    def send_msg(self, msg, immediate=False, address=None):
        if self.socket:
            if immediate:
                self.send(msg, address)
            else:
                self.outgoingMailbox.put(msg)
                for callback in self.readyCallbacks:
                    callback(self)

    def send(self, msg, address=None):
        msg = str(msg)
        frmt = "!%ds" % len(msg)
        packedMsg = struct.pack(frmt, msg)
        packedHdr = struct.pack('!I', len(packedMsg))
        self._send(packedHdr, address)
        self._send(packedMsg, address)

    def _send(self, msg, address=None):
        sent = 0
        while sent < len(msg):
            if address is None:
                sent += self.socket.send(msg[sent:])
            else:
                sent += self.socket.sendto(msg[sent:], address)

    def event(self, event):
        for callback in self.eventCallbacks:
            callback(event)

    # Callback management
    # -------------------
    def add_event_callback(self, callback):
        self.eventCallbacks.add(callback)

    def remove_event_callback(self, callback):
        self.eventCallbacks.remove(callback)

    def add_ready_callback(self, callback):
        self.readyCallbacks.add(callback)

    def remove_ready_callback(self, callback):
        self.readyCallbacks.remove(callback)

    def add_closing_callback(self, callback):
        self.closingCallbacks.add(callback)

    def remove_closing_callback(self, callback):
        self.closingCallbacks.remove(callback)


# Exceptions
# ----------
class ReadError(Exception):
    """Exception for read errors on the endpoint"""
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
