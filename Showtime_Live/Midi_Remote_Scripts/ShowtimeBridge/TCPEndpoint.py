from NetworkEndpoint import NetworkEndpoint, NetworkPrefixes
import threading


class TCPEndpoint(threading.Thread):
    def __init__(self, localPort, remotePort, threaded=True):
        NetworkEndpoint.__init__(self, localPort, remotePort, threaded)

        # Sockets
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.recv_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        self.recv_sock.bind(self.localAddr)
        if not self.threaded:
            self.recv_sock.setblocking(0)   
        self.connect()
        
        # Heartbeat
        self.lastPeerHeartbeat = 0
        self.lastTransmittedHeartbeat = 0

    def connect():
        try:
            self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.send_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
            self.send_sock.setblocking(0)
            self.peerConnected = True
        except Exception, e:
            print(e)
            self.peerConnected = False

    def recv_msg(self):
        if not self.peerConnected:
            return
        NetworkEndpoint.recv_msg(self)

    def event(self, event):
        pass