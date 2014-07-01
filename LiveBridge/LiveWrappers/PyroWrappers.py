##
#
# Base Pyro <-> Live Wrapper class
#
##

try:
    from LiveUtils import *
except ImportError:
    print("Couldn't load LiveAPI")

try:
    from .. import PyroShared
except:
    print("Couldn't import PyroShared")


class PyroWrapper:

    def __init__(self, publisher):
        self.publisher = publisher
        self.ref_wrapper = None
        self.incomingActions = {}

    def get_reference(self):
        return self.ref_wrapper()
