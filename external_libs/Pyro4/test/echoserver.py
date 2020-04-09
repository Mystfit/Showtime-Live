"""
Echo server for test purposes.
This is usually invoked by starting this module as a script:

  :command:`python -m Pyro4.test.echoserver`
  or simply: :command:`pyro4-test-echoserver`


It is also possible to use the :class:`EchoServer` in user code
but that is not terribly useful.

Pyro - Python Remote Objects.  Copyright by Irmen de Jong (irmen@razorvine.net).
"""

from __future__ import print_function
import sys
import os
import time
import warnings
import threading
from optparse import OptionParser
from Pyro4 import core, naming
from Pyro4.configuration import config


__all__ = ["EchoServer"]


@core.expose
class EchoServer(object):
    """
    The echo server object that is provided as a Pyro object by this module.
    If its :attr:`verbose` attribute is set to ``True``, it will print messages as it receives calls.
    """
    _verbose = False
    _must_shutdown = False

    def echo(self, message):
        """return the message"""
        if self._verbose:
            message_str = repr(message).encode(sys.stdout.encoding, errors="replace").decode(sys.stdout.encoding)
            print("%s - echo: %s" % (time.asctime(), message_str))
        return message

    def error(self):
        """generates a simple exception without text"""
        if self._verbose:
            print("%s - error: generating exception" % time.asctime())
        raise ValueError("expected error from echoserver error() method")

    def error_with_text(self):
        """generates a simple exception with message"""
        if self._verbose:
            print("%s - error: generating exception" % time.asctime())
        raise ValueError("the message of the error")

    @core.oneway
    def oneway_echo(self, message):
        """just like echo, but oneway; the client won't wait for response"""
        if self._verbose:
            message_str = repr(message).encode(sys.stdout.encoding, errors="replace").decode(sys.stdout.encoding)
            print("%s - oneway_echo: %s" % (time.asctime(), message_str))
        return "bogus return value"

    def slow(self):
        """returns (and prints) a message after a certain delay"""
        if self._verbose:
            print("%s - slow: waiting a bit..." % time.asctime())
        time.sleep(5)
        if self._verbose:
            print("%s - slow: returning result" % time.asctime())
        return "Finally, an answer!"

    def generator(self):
        """a generator function that returns some elements on demand"""
        yield "one"
        yield "two"
        yield "three"

    def nan(self):
        return float("nan")

    def inf(self):
        return float("inf")

    @core.oneway
    def oneway_slow(self):
        """prints a message after a certain delay, and returns; but the client won't wait for it"""
        if self._verbose:
            print("%s - oneway_slow: waiting a bit..." % time.asctime())
        time.sleep(5)
        if self._verbose:
            print("%s - oneway_slow: returning result" % time.asctime())
        return "bogus return value"

    def _private(self):
        """a 'private' method that should not be accessible"""
        return "should not be allowed"

    def __private(self):
        """another 'private' method that should not be accessible"""
        return "should not be allowed"

    def __dunder__(self):
        """a double underscore method that should be accessible normally"""
        return "should be allowed (dunder)"

    def shutdown(self):
        """called to signal the echo server to shut down"""
        if self._verbose:
            print("%s - shutting down" % time.asctime())
        self._must_shutdown = True

    @property
    def verbose(self):
        return self._verbose

    @verbose.setter
    def verbose(self, onoff):
        self._verbose = bool(onoff)


class NameServer(threading.Thread):
    def __init__(self, hostname, hmac=None):
        super(NameServer, self).__init__()
        self.setDaemon(1)
        self.hostname = hostname
        self.hmac = hmac
        self.started = threading.Event()

    def run(self):
        self.uri, self.ns_daemon, self.bc_server = naming.startNS(self.hostname, hmac=self.hmac)
        self.started.set()
        if self.bc_server:
            self.bc_server.runInThread()
        self.ns_daemon.requestLoop()


def startNameServer(host, hmac=None):
    ns = NameServer(host, hmac=hmac)
    ns.start()
    ns.started.wait()
    return ns


def main(args=None, returnWithoutLooping=False):
    parser = OptionParser()
    parser.add_option("-H", "--host", default="localhost", help="hostname to bind server on (default=%default)")
    parser.add_option("-p", "--port", type="int", default=0, help="port to bind server on")
    parser.add_option("-u", "--unixsocket", help="Unix domain socket name to bind server on")
    parser.add_option("-n", "--naming", action="store_true", default=False, help="register with nameserver")
    parser.add_option("-N", "--nameserver", action="store_true", default=False, help="also start a nameserver")
    parser.add_option("-v", "--verbose", action="store_true", default=False, help="verbose output")
    parser.add_option("-q", "--quiet", action="store_true", default=False, help="don't output anything")
    parser.add_option("-k", "--key", help="the HMAC key to use (deprecated)")
    options, args = parser.parse_args(args)

    if options.key:
        warnings.warn("using -k to supply HMAC key on the command line is a security problem "
                      "and is deprecated since Pyro 4.72. See the documentation for an alternative.")
    if "PYRO_HMAC_KEY" in os.environ:
        if options.key:
            raise SystemExit("error: don't use -k and PYRO_HMAC_KEY at the same time")
        options.key = os.environ["PYRO_HMAC_KEY"]

    if options.verbose:
        options.quiet = False
    if not options.quiet:
        print("Starting Pyro's built-in test echo server.")
    config.SERVERTYPE = "multiplex"

    hmac = (options.key or "").encode("utf-8")
    if not hmac and not options.quiet:
        print("Warning: HMAC key not set. Anyone can connect to this server!")

    nameserver = None
    if options.nameserver:
        options.naming = True
        nameserver = startNameServer(options.host, hmac=hmac)

    d = core.Daemon(host=options.host, port=options.port, unixsocket=options.unixsocket)
    if hmac:
        d._pyroHmacKey = hmac
    echo = EchoServer()
    echo._verbose = options.verbose
    objectName = "test.echoserver"
    uri = d.register(echo, objectName)
    if options.naming:
        host, port = None, None
        if nameserver is not None:
            host, port = nameserver.uri.host, nameserver.uri.port
        ns = naming.locateNS(host, port, hmac_key=hmac)
        ns.register(objectName, uri)
        if options.verbose:
            print("using name server at %s" % ns._pyroUri)
            if nameserver is not None:
                if nameserver.bc_server:
                    print("broadcast server running at %s" % nameserver.bc_server.locationStr)
                else:
                    print("not using a broadcast server")
    else:
        if options.verbose:
            print("not using a name server.")
    if not options.quiet:
        print("object name: %s" % objectName)
        print("echo uri: %s" % uri)
        print("echoserver running.")

    if returnWithoutLooping:
        return d, echo, uri  # for unit testing
    else:
        d.requestLoop(loopCondition=lambda: not echo._must_shutdown)
    d.close()


if __name__ == "__main__":
    main()
