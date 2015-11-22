from NetworkEndpoint import NetworkEndpoint, SimpleMessage, NetworkPrefixes
import threading


class HeartbeatThread(threading.Thread):
    def __init__(self, endpoint):
        threading.Thread.__init__(self)
        self.name = "heartbeat_thread"
        self.endpoint = endpoint
        self.exitFlag = 0

    def stop(self):
        self.exitFlag = 1

    def run(self):
        while not self.exitFlag:
            time.sleep(0.5)
            self.endpoint.send_heartbeat()
            self.endpoint.check_heartbeat()
        self.join(2)


class UDPEndpoint(NetworkEndpoint):
    HEARTBEAT_DURATION = 5000
    HEARTBEAT_TIMEOUT = HEARTBEAT_DURATION * 2
    MAX_MSG_SIZE = 65536

    def __init__(self, localPort, remotePort, threaded=True):
        NetworkEndpoint.__init__(self, localPort, remotePort, threaded)

        # Heartbeat
        self.lastPeerHeartbeat = 0
        self.lastTransmittedHeartbeat = 0

        # Sockets
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_sock.setblocking(0)

        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock.bind(self.localAddr)

        # Threading
        if self.threaded:
            self.heartbeatThread = HeartbeatThread(self)
            self.heartbeatThread.start()
        else:
            self.recv_sock.setblocking(0)

    def close(self):
        if self.heartbeatThread:
            self.heartbeatThread.stop()
        NetworkEndpoint.close(self)

    def send_heartbeat(self):
        if(NetworkEndpoint.current_milli_time() > self.lastTransmittedHeartbeat + NetworkEndpoint.HEARTBEAT_DURATION):
            self.send_msg(SimpleMessage(NetworkPrefixes.HEARTBEAT, None))

    def check_heartbeat(self):
        if(NetworkEndpoint.current_milli_time() > self.lastPeerHeartbeat + NetworkEndpoint.HEARTBEAT_TIMEOUT):
            self.peerConnected = False

    def event(self, event):
        if event.subject == NetworkShared.HEARTBEAT:
            self.lastPeerHeartbeat = NetworkEndpoint.current_milli_time()
            self.peerConnected = True
