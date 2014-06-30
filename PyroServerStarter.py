import Pyro.naming
import Pyro.EventService.Server
from Pyro.errors import *
import Pyro.util
from threading import Thread


class NameServer(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.setDaemon(True)
        self.starter = Pyro.naming.NameServerStarter()

    def run(self):
        print "Launching Pyro Name Server"
        self.starter.start()

    def waitUntilStarted(self):
        return self.starter.waitUntilStarted()


class EventServer(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.setDaemon(True)
        self.starter = Pyro.EventService.Server.EventServiceStarter()

    def run(self):
        print "Launching Pyro Event Server"
        # we're using the OS's automatic port allocation
        es_port = 0
        Pyro.config.PYRO_ES_BLOCKQUEUE = False
        Pyro.config.PYRO_ES_QUEUESIZE = 10
        self.starter.start(port=es_port, norange=(es_port == 0))

    def waitUntilStarted(self):
        return self.starter.waitUntilStarted()


def startServer():
    nss = NameServer()
    nss.start()
    nss.waitUntilStarted()      # wait until the NS has fully started.
    ess = EventServer()
    ess.start()
    ess.waitUntilStarted()      # wait until the ES has fully started.
