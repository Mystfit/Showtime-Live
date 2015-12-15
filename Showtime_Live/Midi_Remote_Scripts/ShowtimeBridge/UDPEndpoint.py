from NetworkEndpoint import NetworkEndpoint, SimpleMessage, NetworkPrefixes
import threading
import socket
import time
from Logger import Log

class HeartbeatThread(threading.Thread):
    def __init__(self, endpoint):
        threading.Thread.__init__(self)
        self.name = "heartbeat_thread"
        self.endpoint = endpoint
        self.exitFlag = 0
        self.daemon = True

    def stop(self):
        self.exitFlag = 1

    def run(self):
        while not self.exitFlag:
            time.sleep(1)
            self.endpoint.send_heartbeat()
            # self.endpoint.check_heartbeat()
        self.join(2)


class UDPEndpoint(NetworkEndpoint):
    HEARTBEAT_DURATION = 2000
    HEARTBEAT_TIMEOUT = HEARTBEAT_DURATION * 2

    def __init__(self, localPort, remotePort, threaded=True):
        self.lastPeerHeartbeat = 0
        self.lastTransmittedHeartbeat = 0
        NetworkEndpoint.__init__(self, localPort, remotePort, threaded)

    def create_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(5)
        self.socket.bind(self.localAddr)

        if self.threaded:
            self.heartbeatThread = HeartbeatThread(self)
            self.heartbeatThread.start()
        else:
            self.socket.setblocking(0)

    def close(self):
        if hasattr(self, "heartbeatThread"):
            if self.heartbeatThread:
                self.heartbeatThread.stop()
        NetworkEndpoint.close(self)

    def send_heartbeat(self):
        if(NetworkEndpoint.current_milli_time() > self.lastTransmittedHeartbeat + UDPEndpoint.HEARTBEAT_DURATION):
            self.send_msg(SimpleMessage(NetworkPrefixes.HEARTBEAT, None), True, self.remoteAddr)

    def check_heartbeat(self):
        if(NetworkEndpoint.current_milli_time() > self.lastPeerHeartbeat + UDPEndpoint.HEARTBEAT_TIMEOUT):
            self.connectionStatus = NetworkEndpoint.PIPE_DISCONNECTED
            for callback in self.closingCallbacks:
                callback()
        return (self.connectionStatus == NetworkEndpoint.PIPE_CONNECTED)

    def event(self, event):
        if event.subject == NetworkPrefixes.HEARTBEAT:
            self.lastPeerHeartbeat = NetworkEndpoint.current_milli_time()
            self.connectionStatus = NetworkEndpoint.PIPE_CONNECTED
            return
        NetworkEndpoint.event(self, event)

    def send(self, msg, address=None):
        NetworkEndpoint.send(self, msg, self.remoteAddr)
