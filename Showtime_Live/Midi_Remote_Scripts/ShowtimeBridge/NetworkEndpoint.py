import socket
import threading
import errno
import time
import Queue
import struct

try:
    import json
except ImportError:
    import simplejson as json
from Logger import Log


class NetworkPrefixes:
    INCOMING = "I"
    OUTGOING = "O"
    RESPONDER = "L"
    REGISTRATION = "R"
    DELIMITER = "_"
    HEARTBEAT = "H"

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

    def __init__(self, localPort, remotePort, threaded=True):
        self.threaded = threaded
        self.localAddr = ((''), localPort)
        self.remoteAddr = (("127.0.0.1"), remotePort)
        self.eventCallbacks = set()
        self.readyCallbacks = set()
        self.outgoingMailbox = Queue.Queue()
        self.peerConnected = False
        self.create_socket()

    def create_socket(self):
        raise NotImplementedError

    def close(self):
        if self.socket:
            self.socket.close()
        self.peerConnected = False

    def add_event_callback(self, callback):
        self.eventCallbacks.add(callback)

    def remove_event_callback(self, callback):
        self.eventCallbacks.remove(callback)

    def add_ready_callback(self, callback):
        self.readyCallbacks.add(callback)

    def remove_ready_callback(self, callback):
        self.readyCallbacks.remove(callback)

    def recv_msg(self):
        if self.threaded:
            self.recv()
        else:
            try:
                while 1:
                    self.recv()
            except Exception, e:
                err, message = e
                if err != errno.EAGAIN:                                
                    Log.error('error handling message, errno ' + str(errno) + ': ' + message)

    def recv(self):
        # return self.socket.recv(NetworkEndpoint.MAX_MSG_SIZE)
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
            # try:
            #     dataTmp = self.socket.recv(size-len(data))
            #     print(dataTmp)
            #     data += dataTmp
            #     if dataTmp == '':
            #         raise RuntimeError("socket connection broken")
            # except socket.error, e:
            #     if e[0] == 35:
            #         Log.warn(errno.errorcode[35])
            #         Log.warn("Resource unavailable, trying again.")
            #     else:
            #         Log.error(e)
            #     break
            dataTmp = self.socket.recv(min(size-len(data), NetworkEndpoint.MAX_MSG_SIZE))
            data += dataTmp
            if dataTmp == '':
                raise RuntimeError("socket connection broken")
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

    @staticmethod
    def current_milli_time():
        return int(round(time.time() * 1000))
