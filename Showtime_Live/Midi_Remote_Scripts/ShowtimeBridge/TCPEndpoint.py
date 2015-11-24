from NetworkEndpoint import NetworkEndpoint, NetworkPrefixes
import threading
import time
import socket
import errno


class TCPEndpoint(NetworkEndpoint):
    def __init__(self, localPort, remotePort, threaded=True):
        NetworkEndpoint.__init__(self, localPort, remotePort, threaded)

        # Sockets
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.recv_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        self.recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.recv_sock.bind(self.localAddr)
        self.recv_sock.listen(2)

        if not self.threaded:
            self.recv_sock.setblocking(0)   
        
        # Heartbeat
        self.lastPeerHeartbeat = 0
        self.lastTransmittedHeartbeat = 0

    def connect(self):
        try:
            self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.send_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
            self.send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.send_sock.settimeout(5)
            
            retries = 20
            while retries > 0:
                status = self.send_sock.connect_ex(self.remoteAddr)
                if status != errno.EAGAIN:
                    print("...connected")
                    retries = 0
                    self.peerConnected = True
                else:
                    print("Reconnecting...")
                    retries -= 1
            if self.threaded and not self.is_alive():
                self.start()
        except socket.timeout, e:
            print("Timed out")
            self.peerConnected = False
        
        return self.peerConnected

    def recv_msg(self):
        if not self.peerConnected:
            if not self.threaded:
                return
            else:
                while not self.peerConnected:
                    time.sleep(1)
        NetworkEndpoint.recv_msg(self)
