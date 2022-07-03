import threading
import rpyc
from rpyc.core import SlaveService
import showtime.showtime as ZST
import defusedxml

class RPCLoop(threading.Thread):
    def __init__(self, bridge):
        threading.Thread.__init__(self)
        self.bridge = bridge
        self.setDaemon(True)

    def run(self):
        self.bridge.start()


class TestConnectionAdaptor(ZST.ZstConnectionAdaptor):
    def __init__(self):
        ZST.ZstConnectionAdaptor.__init__(self)

    def set_cb(self, cb):
        self.cb = cb

    def on_connected_to_server(self, client, server):
        self.cb(client, server)


class LiveZSTService(rpyc.SlaveService):
    def __init__(self, client, server):
        self.zst_client = client
        self.bridge_server = server

    def on_connect(self, conn):
        print("New connection")

    def on_disconnect(self, conn):
        print("Connection closed")

    def exposed_get_client(self):
        return self.zst_client

    def exposed_get_module(self):
        return ZST

    def exposed_log_write(self, message):
        print("Live: " + str(message))

    def exposed_test_adaptor_cls(self):
        return TestConnectionAdaptor

    def exposed_set_control_surface_callback(self, control_surface_accessor):
        print("Registering control surface accessor: {}".format(control_surface_accessor))
        self.bridge_server.live_control_surface = control_surface_accessor
