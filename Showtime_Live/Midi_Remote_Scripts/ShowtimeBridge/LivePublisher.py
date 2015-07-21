import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "ext_libs"))

from Pyro.EventService.Clients import Publisher
import Pyro.errors
from PyroShared import PyroPrefixes
from Logger import Log

class LivePublisher(Publisher):

    def send_to_showtime(self, message, args):
        return self.send_message(PyroPrefixes.prefix_outgoing(message), args)

    def send_to_live(self, message, args):
        return self.send_message(PyroPrefixes.prefix_incoming(message), args)

    def register_to_showtime(self, message, methodaccess, methodargs=None):
        return self.send_message(PyroPrefixes.prefix_registration(message), {"args": methodargs, "methodaccess": methodaccess})

    def send_message(self, message, args):
        args = args if args else {}
        retries = 5
        success = False
        Log.write("Publishing message " + str(message))

        while retries > 0:
            try:
                self.publish(message, args)
                success = True
                Log.write("Success!")
            except Pyro.errors.ConnectionClosedError, e:
                Log.write(e)
                Log.write(
                    "Rebinding. {0} retries left.".format(str(retries)))
                self.adapter.rebindURI()
                retries -= 1
            if success:
                break
        return success