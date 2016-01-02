from NetworkEndpoint import NetworkEndpoint, SimpleMessage, NetworkPrefixes
import threading
import socket
import time
from Logger import Log


class HeartbeatThread(threading.Thread):
    """Thread dedicated to sending heartbeat messages over the UDP socket"""
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
    """Network endpoint using UDP"""
    HEARTBEAT_DURATION = 2000
    HEARTBEAT_TIMEOUT = HEARTBEAT_DURATION * 2

    def __init__(self, localport, remoteport, threaded=True, heartbeatid=None):
        NetworkEndpoint.__init__(self, localport, remoteport, threaded)
        self.lastPeerHeartbeatTime = 0
        self.lastTransmittedHeartbeatTime = 0
        self.heartbeatID = heartbeatid
        self.lastReceivedHeartbeatID = None
        self.heartbeatThread = None

    def create_socket(self):
        """Create the UDP socket for this endpoint"""
        # noinspection PyAttributeOutsideInit
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(5)
        self.socket.bind(self.localAddr)

        if self.threaded:
            self.heartbeatThread = HeartbeatThread(self)
            self.heartbeatThread.start()
        else:
            self.socket.setblocking(0)

    def close(self):
        """Destroy this socket"""
        if hasattr(self, "heartbeatThread"):
            if self.heartbeatThread:
                self.heartbeatThread.stop()
        NetworkEndpoint.close(self)

    def send_heartbeat(self):
        """Send heartbeat message"""
        if NetworkEndpoint.current_milli_time() > self.lastTransmittedHeartbeatTime + UDPEndpoint.HEARTBEAT_DURATION:
            self.send_msg(SimpleMessage(NetworkPrefixes.HEARTBEAT, self.heartbeatID), True, self.remoteAddr)

    def check_heartbeat(self):
        """Check if we've received a UDP heartbeat from a remote UDP endpoint"""
        if NetworkEndpoint.current_milli_time() > self.lastPeerHeartbeatTime + UDPEndpoint.HEARTBEAT_TIMEOUT:
            self.connectionStatus = NetworkEndpoint.PIPE_DISCONNECTED
            Log.info("Heartbeat timeout")

        # Verify we're still talking to the same server
        if self.heartbeatID and self.lastReceivedHeartbeatID != self.heartbeatID:
            self.connectionStatus = NetworkEndpoint.PIPE_DISCONNECTED
            Log.network(
                    "Last heartbeat ID: %s. New heartbeat ID: %s" % (self.lastReceivedHeartbeatID, self.heartbeatID))

        self.heartbeatID = self.lastReceivedHeartbeatID

        if self.connectionStatus == NetworkEndpoint.PIPE_DISCONNECTED:
            for callback in self.closingCallbacks:
                callback()

        return self.connectionStatus == NetworkEndpoint.PIPE_CONNECTED

    def event(self, event):
        """Incoming event handler

        Args:
            event: SimpleMessage object containing event subject and msg
        """
        if event.subject == NetworkPrefixes.HEARTBEAT:
            self.lastPeerHeartbeatTime = NetworkEndpoint.current_milli_time()
            self.lastReceivedHeartbeatID = event.msg
            self.connectionStatus = NetworkEndpoint.PIPE_CONNECTED
            return
        NetworkEndpoint.event(self, event)

    def send(self, msg, address=None):
        """Send a message

        Args:
            address: Destination address of message
        """
        NetworkEndpoint.send(self, msg, self.remoteAddr)
