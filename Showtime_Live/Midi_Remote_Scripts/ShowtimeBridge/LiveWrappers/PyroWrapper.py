from .. import LiveUtils
from .. import PyroShared

class PyroWrapper(object):
    # Proxy method types for Showtime
    METHOD_READ = "read"
    METHOD_WRITE = "write"
    METHOD_RESPOND = "responder"

    # Class method references
    _incoming_methods = {}
    _outgoing_methods = {}

    # References to all instances created of this object
    _instances = None

    # Publisher for all wrappers
    _publisher = None

    # Queued wrapper events
    _queued_wrappers = set()

    # Constructor
    def __init__(self, handle, parent=None):
        self._handle = handle
        self._parent = parent

        # Try to register the instance at the class level
        if not self.__class__._instances:
            self.__class__._instances = {}
        self.__class__.add_instance(self)

    @classmethod
    def add_instance(cls, instance):
        cls._instances[id(instance)] = instance

    '''Returns a list of all instances of this node available'''
    @classmethod
    def instances(cls):
        return cls._instances.values() if cls._instances else []

    '''Find an reference of this class from a given id'''
    @classmethod
    def findById(cls, instanceId):
        return cls._instances[instanceId]

    '''Set the global publisher for all wrappers'''
    @staticmethod
    def set_publisher(publisher):
        PyroWrapper._publisher = publisher

    '''Destructor for this wrapper'''
    def destroy(self):
        del _instances[self.id()]

    '''Registers a method for this wrapper that will publish to the network'''
    @classmethod
    def add_outgoing_method(cls, methodname):
        # if methodname in cls._outgoing_methods:
        #     raise Exception("Trying to register an outgoing method twice!")
        cls._outgoing_methods[methodname] = PyroMethodDef(methodname, PyroWrapper.METHOD_READ)

    '''Registers method for this wrapper that will receive events from the network'''
    @classmethod
    def add_incoming_method(cls, methodname, methodargs, callback, isResponder=False):
        # if methodname in cls._incoming_methods:
        #     raise Exception("Trying to register an incoming method twice!")

        accessType = PyroWrapper.METHOD_RESPOND if isResponder else PyroWrapper.METHOD_WRITE
        cls._incoming_methods[methodname] = PyroMethodDef(methodname, accessType, methodargs, callback)

    '''Register all methods for this class'''
    @classmethod
    def register_methods(cls):
        raise NotImplementedError

    '''Registered incoming methods'''
    @classmethod
    def incoming_methods(cls):
        return cls._incoming_methods

    '''Registered outgoing methods'''
    @classmethod
    def outgoing_methods(cls):
        return cls._outgoing_methods

    '''Process all queued messages for wrappers that need to 
    be applied post-eventloop'''
    @classmethod
    def process_queued_events(cls):
        for p in cls._queued_wrappers:
            p.apply_queued_event()
        PyroWrapper._queued_wrappers.clear()

    '''Flag this instance as having a queued event'''
    def flag_as_queued(self):
        PyroWrapper._queued_wrappers.add(self)

    '''Override that will be ran when the instance is processed
    through the post-eventloop queue'''
    def apply_queued_event():
        raise NotImplementedError

    '''Get the Live object reference this wrapper controls'''
    def handle(self):
        return self._handle

    '''Get the parent wrapper of this wrapper'''
    def parent(self):
        return self._parent

    '''Send the updated wrapper value to the network'''
    def update(self, action, values):
        val = {"val": values, "id": id(self._handle)}
        PyroWrapper._publisher.send_to_showtime(action, val)


class PyroMethodDef:
    def __init__(self, methodname, methodAccess, methodargs=None, callback=None):
        self.methodName = methodname
        self.methodAccess = methodAccess
        self.methodArgs = methodargs if methodargs else {}
        self.callback = callback
