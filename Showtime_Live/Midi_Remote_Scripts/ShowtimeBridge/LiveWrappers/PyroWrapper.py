# from .. import LiveUtils
# from .. import PyroShared
from ..Logger import Log


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
    def __init__(self, handle, handleindex=None, parent=None):
        self._handle = handle
        self._children = set()
        self.handleHash = hash(handle)
        Log.write(str(self) + " hash:" + str(self.handleHash))
        self.__class__.add_instance(self)
        
        if parent:
            self._parent = parent
            self._parent.add_child(self)
            self.handleindex = handleindex

        self.create_listeners()
        self.update_hierarchy()

    def update_hierarchy(self, cls=None, livevector=None):
        """Refreshes the hierarchy of wrappers underneath this wrapper"""
        if cls and livevector:
            cls.remove_child_wrappers(livevector)
            cls.create_child_wrappers(self, livevector)

    @classmethod
    def create_child_wrappers(cls, parent, livevector):
        """Create missing child wrappers underneath this wrapper"""
        Log.write("Creating missing wrappers")
        for index, handle in enumerate(livevector):
            Log.write("Index is " + str(index) + ". Handle is " + str(handle))
            wrapper = cls.findWrapperByHandle(handle)

            if not wrapper:
                cls.add_instance(cls(handle, index, parent))
                Log.write(str(cls) + " added a new instance")
            else:
                Log.write(str(wrapper.handleHash) + " already has a wrapper")

    @classmethod
    def remove_child_wrappers(cls, livevector):
        """Remove wrappers that are missing a live object"""
        for wrapperId, wrapper in enumerate(cls.instances()):
            if wrapperId not in livevector:
                Log.write(str(wrapper.handleHash) + " is missing. Removing!")
                wrapper.destroy()
                del wrapper
    
    def add_child(self, child):
        """Add a child wrapper to this wrapper
        """
        self._children.add(child)
    
    def children(self):
        """Return all children of this wrapper"""
        return _children

    @classmethod
    def add_instance(cls, instance):
        """Registers an instance of the class at the class level"""
        if not cls._instances:
            cls._instances = {}

        cls._instances[instance.handleHash] = instance
        return instance

    """Returns a list of all instances of this node available"""
    @classmethod
    def instances(cls):
        """Returns a list of all instances of this node available"""
        return cls._instances.values() if cls._instances else []

    @staticmethod
    def all_instances():
        """Returns all active wrappers"""
        instances = {}
        for cls in PyroWrapper.__subclasses__():
            instances.update(cls.instances())
        return instances

    @classmethod
    def clear_instances(cls):
        """Clear all instances of a class type"""
        cls._instances = {}

    @classmethod
    def findWrapperByHandle(cls, handle):
        """Find an reference of this class from a given id"""
        try:
            return cls._instances[hash(handle)]
        except KeyError:
            return None

    @staticmethod
    def set_publisher(publisher):
        """Set the global publisher for all wrappers"""
        PyroWrapper._publisher = publisher

    def destroy(self):
        """Destructor for this wrapper"""
        for child in self._children:
            child.destroy()
        self._children.clear()

        self.destroy_listeners()
        Log.write(self.__class__._instances)
        Log.write(self.handleHash)
        del self.__class__._instances[self.handleHash]

    def destroy_listeners(self):
        """Destroy all listeners on this wrapper"""
        pass

    def create_listeners(self):
        """Create all listeners for this object"""
        pass

    @classmethod
    def add_outgoing_method(cls, methodname):
        """Registers a method for this wrapper that will publish to the network"""
        if methodname in cls._outgoing_methods:
            Log.write("Outgoing method aready exists")
            return

        cls._outgoing_methods[methodname] = PyroMethodDef(methodname, PyroWrapper.METHOD_READ)

    @classmethod
    def add_incoming_method(cls, methodname, methodargs, callback, isResponder=False):
        """Registers method for this wrapper that will receive events from the network"""
        if methodname in cls._incoming_methods:
            Log.write("Incoming method aready exists")

        accessType = PyroWrapper.METHOD_RESPOND if isResponder else PyroWrapper.METHOD_WRITE
        cls._incoming_methods[methodname] = PyroMethodDef(methodname, accessType, methodargs, callback)

    @classmethod
    def register_methods(cls):
        """Register all methods for this class"""
        raise NotImplementedError

    @classmethod
    def incoming_methods(cls):
        """Registered incoming methods"""
        return cls._incoming_methods

    @classmethod
    def outgoing_methods(cls):
        """Registered outgoing methods"""
        return cls._outgoing_methods

    @classmethod
    def process_queued_events(cls):
        """Process all queued messages for wrappers that need to 
        be applied post-eventloop
        """
        for p in cls._queued_wrappers:
            p.apply_queued_event()
        PyroWrapper._queued_wrappers.clear()

    def flag_as_queued(self):
        """Flag this instance as having a queued event"""
        PyroWrapper._queued_wrappers.add(self)

    def apply_queued_event():
        """Override that will be ran when the instance is processed
        through the post-eventloop queue
        """
        raise NotImplementedError

    def handle(self):
        """Get the Live object reference this wrapper controls"""
        return self._handle

    def parent(self):
        """Get the parent wrapper of this wrapper"""
        return self._parent

    def update(self, action, values):
        """Send the updated wrapper value to the network"""
        val = {"val": values, "id": self.handleHash}
        PyroWrapper._publisher.send_to_showtime(action, val)


class PyroMethodDef:
    def __init__(self, methodname, methodAccess, methodargs=None, callback=None):
        self.methodName = methodname
        self.methodAccess = methodAccess
        self.methodArgs = methodargs if methodargs else {}
        self.callback = callback
