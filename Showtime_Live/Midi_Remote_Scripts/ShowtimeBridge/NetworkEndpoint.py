import socket
import threading
import errno
import time
try:
    import json
except ImportError:
    import simplejson as json


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


class NetworkEndpoint(threading.Thread):
    MAX_MSG_SIZE = 65536

    def __init__(self, localPort, remotePort, threaded=True):
        self.threaded = threaded
        self.localAddr = ((''), localPort)
        self.remoteAddr = (("127.0.0.1"), remotePort)
        self.eventCallbacks = set()
        
        self.send_sock = None
        self.recv_sock = None
        self.peerConnected = False

        # Threading
        if(self.threaded):
            threading.Thread.__init__(self)
            self.exitFlag = 0
            self.daemon = True

    def close(self):
        if self.send_sock:
            self.send_sock.close()
        if self.recv_sock:
            self.recv_sock.close()

    def run(self):
        while not self.exitFlag:
            self.recv_msg()
        self.close()
        self.join(2)

    def stop(self):
        self.exitFlag = 1

    def add_event_callback(self, callback):
        self.eventCallbacks.add(callback)

    def remote_event_callback(self, callback):
        self.eventCallbacks.remove(callback)

    def send_msg(self, msg):
        if self.send_sock:
            ret = self.send_sock.sendto(str(msg), self.remoteAddr)
            if (ret == -1):
                print("Error sending message %s:%d" % (msg, ret))
            if (ret != len(msg)):
                print("Partial send of message %s:%d of %d" % (msg, ret, len(msg)))
        return ret

    def recv_msg(self):
        if self.threaded:
            raw = self.recv_sock.recv(NetworkEndpoint.MAX_MSG_SIZE)
            msg = SimpleMessage.parse(raw)
            if not msg.subject == "H":
                print msg
            self.event(msg)
        else:
            try:
                while 1:
                    raw = self.recv_sock.recv(NetworkEndpoint.MAX_MSG_SIZE)
                    msg = SimpleMessage.parse(raw)
                    self.event(msg)
            except Exception, e:
                err, message = e
                if err != errno.EAGAIN:                                
                    print('error handling message, errno ' + str(errno) + ': ' + message)

    def event(self, event):
        print ("Received event!")
        print ("Available callbacks:" + str(self.eventCallbacks))
        for callback in self.eventCallbacks:
            print("Running callback " + str(callback))
            callback(event)

    @staticmethod
    def current_milli_time():
        return int(round(time.time() * 1000))
