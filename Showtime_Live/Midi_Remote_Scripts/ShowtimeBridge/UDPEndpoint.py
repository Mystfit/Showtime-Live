import socket
import threading
import errno
try:
    import json
except ImportError:
    import simplejson as json

localAddr = ("127.0.0.1")
maxMsgSize = 65536

class UDPEndpoint(threading.Thread):
    def __init__(self, localPort, remotePort, threaded=True):
        self.threaded = threaded
        self.localAddr = (localAddr, localPort)
        self.remoteAddr = (localAddr, remotePort)
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock.bind(self.localAddr)
        self.send_sock.setblocking(0)

        if(self.threaded):
            threading.Thread.__init__(self)
            self.exitFlag = 0
            self.daemon = True
        else:
            self.recv_sock.setblocking(0)


    def close(self):
        self.send_sock.close()
        self.recv_sock.close()

    def run(self):
        while not self.exitFlag:
            self.recv_msg()
        self.close()
        self.join(2)

    def stop(self):
        self.exitFlag = 1

    def send_msg(self, msg):
        ret = self.send_sock.sendto(str(msg), self.remoteAddr)
        if (ret == -1):
            print("Error sending message %s:%d" % (msg, ret))
        if (ret != len(msg)):
            print("Partial send of message %s:%d of %d" % (msg, ret, len(msg)))

    def recv_msg(self):
        if self.threaded:
            self.event(SimpleMessage.parse(self.recv_sock.recv(maxMsgSize)))
        else:
            try:
                while 1:
                    self.event(SimpleMessage.parse(self.recv_sock.recv(maxMsgSize)))
            except Exception, e:
                err, message = e
                if err != errno.EAGAIN:                                
                    print('error handling message, errno ' + str(errno) + ': ' + message)

    def event(self, event):
        print("Received " + event)


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
