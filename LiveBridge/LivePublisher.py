from Pyro.EventService.Clients import Publisher
import Pyro.errors


class LivePublisher(Publisher):

    def __init__(self, logger=None):
        Publisher.__init__(self)
        self.logger = logger

    def publish_check(self, message, args):
        args = args if args else {}
        retries = 5
        success = False
        self.log_message("Publishing message " + str(message))

        while retries > 0:
            try:
                self.publish(message, args)
                success = True
                self.log_message("Success!")
            except Pyro.errors.ConnectionClosedError, e:
                self.log_message(e)
                self.log_message(
                    "Rebinding. {0} retries left.".format(str(retries)))
                self.adapter.rebindURI()
                retries -= 1
            if success:
                break
        return success

    def log_message(self, message):
        if self.logger:
            self.logger(message)
        else:
            print message
