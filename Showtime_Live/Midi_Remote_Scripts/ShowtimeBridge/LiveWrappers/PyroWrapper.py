import re
from ..Logger import Log


class PyroWrapper(object):
    # Proxy method types for Showtime
    METHOD_READ = "read"
    METHOD_WRITE = "write"
    METHOD_RESPOND = "responder"

    # Delimiter for handle name id's in Live
    ID_DELIM = "-{"
    ID_END = "}"
    ID_NULL = "no_name"

    # Class method references
    _incoming_methods = {}
    _outgoing_methods = {}

    # References to all instances created of this object
    _instances = None

    # Publisher for all wrappers
    _publisher = None

    # Queued wrapper events
    _deferred_actions = {}

    # Total ID count
    _id_counter = long(0)

    # Constructor
    def __init__(self, handle, handleindex=None, parent=None):
        self._handle = handle
        self._children = set()
        
        self._parent = parent
        if parent:
            self._parent.add_child(self)
        
        self.handleindex = handleindex

        self._id = self.create_handle_id()
        self.__class__.add_instance(self)

        self.create_listeners()
        self.update_hierarchy()


    # Cleanup
    # -------
    @staticmethod
    def destroy(wrapper):
        """Destroy a wrapper"""
        for child in wrapper._children:
            PyroWrapper.destroy(child)
        wrapper._children.clear()
        wrapper.destroy_listeners()
        try:
            del wrapper.__class__._instances[wrapper.id()]
        except KeyError:
            Log.warn("%s missing. Already deleted." % wrapper.id())
        
    def create_listeners(self):
        """Create all listeners for this object"""
        if self.handle():
            try:
                self.handle().add_name_listener(self.id_updated)
            except:
                pass

    def destroy_listeners(self):
        """Destroy all listeners on this wrapper"""
        if self.handle():
            try:
                self.handle().remove_name_listener(self.id_updated)
            except:
                pass

    # Hierarchy
    # ---------
    def handle(self):
        """Get the Live object reference this wrapper controls"""
        return self._handle

    def parent(self):
        """Get the parent wrapper of this wrapper"""
        return self._parent

    def update_hierarchy(self, cls=None, livevector=None):
        """Refreshes the hierarchy of wrappers underneath this wrapper"""
        if cls and livevector:
            parentId = self.parent().id() if self.parent() else None
            cls.remove_child_wrappers(livevector, parentId)
            cls.create_child_wrappers(self, livevector)

    @classmethod
    def create_child_wrappers(cls, parent, livevector):
        """Create missing child wrappers underneath this wrapper"""
        Log.info("Creating child wrappers underneath " + str(parent))
        for index, handle in enumerate(livevector):
            wrapper = cls.find_wrapper_by_handle(handle)
            if not wrapper:
                cls.add_instance(cls(handle, index, parent))
                Log.info(str(cls) + " added a new instance")
            else:
                Log.warn(str(wrapper.id()) + " already has a wrapper")

    @classmethod
    def remove_child_wrappers(cls, livevector, idfilter=None):
        """Remove wrappers that are missing a live object"""
        idlist = [PyroWrapper.get_id_from_name(handle.name) for handle in livevector]
        instances = cls.instances()
        if idfilter:
            instances = [i for i in cls.instances() if i.parent().id() == idfilter]

        for wrapper in instances:
            if wrapper.id() not in idlist:
                Log.info(str(wrapper.id()) + " handle is missing in Live. Removing!")
                PyroWrapper.destroy(wrapper)
    
    def add_child(self, child):
        """Add a child wrapper to this wrapper"""
        self._children.add(child)
    
    def children(self):
        """Return all children of this wrapper"""
        return _children


    # Class instances
    # ---------------
    @classmethod
    def add_instance(cls, instance):
        """Registers an instance of the class at the class level"""
        if not cls._instances:
            cls._instances = {}

        cls._instances[instance.id()] = instance
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
    def find_wrapper_by_handle(cls, handle):
        """Find an reference of this class from a given id"""
        try:
            return cls._instances[PyroWrapper.get_id_from_name(handle.name)]
        except KeyError:
            return None

    @classmethod
    def add_outgoing_method(cls, methodname):
        """Registers a method for this wrapper that will publish to the network"""
        if methodname in cls._outgoing_methods:
            Log.warn("Outgoing method aready exists")
            return

        cls._outgoing_methods[methodname] = PyroMethodDef(methodname, PyroWrapper.METHOD_READ)

    @classmethod
    def add_incoming_method(cls, methodname, methodargs, callback, isResponder=False):
        """Registers method for this wrapper that will receive events from the network"""
        if methodname in cls._incoming_methods:
            Log.warn("Incoming method aready exists")

        # !!!STOPGAP!!!
        # Convert method arg arrays to key/value pairs. Needs to be fixed in Showtime instead of here!
        methodargkeys = {}
        if methodargs:
            for key in methodargs:
                methodargkeys[key] = None

        accessType = PyroWrapper.METHOD_RESPOND if isResponder else PyroWrapper.METHOD_WRITE
        cls._incoming_methods[methodname] = PyroMethodDef(methodname, accessType, methodargkeys, callback)


    # Network
    # -------
    @staticmethod
    def set_publisher(publisher):
        """Set the global publisher for all wrappers"""
        PyroWrapper._publisher = publisher

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

    @staticmethod
    def process_deferred_actions():
        """Process all queued messages for wrappers that need to 
        be applied post-eventloop
        """
        if len(PyroWrapper._deferred_actions.keys()) > 0:
            for callback, action in PyroWrapper._deferred_actions.iteritems():
                Log.info("Calling deferred action %s" % callback)
                try:
                    callback(action[1])
                except Exception, e:
                    Log.error("Couldn't run deferred action. %s" % e)
            PyroWrapper._deferred_actions.clear()

    def defer_action(self, method, argument):
        PyroWrapper._deferred_actions[method] = (self, argument)

    def update(self, action, values=None):
        """Send the updated wrapper value to the network"""
        val = {"val": values, "id": self.id()}
        PyroWrapper._publisher.send_to_showtime(action, val)

    def respond(self, action, values):
        """Send the updated wrapper value to the network"""
        val = {"val": values, "id": self.id()}
        PyroWrapper._publisher.send_to_showtime(action, val, True)


    # ID methods
    # ----------
    def id(self):
        """Return the id of this wrapper"""
        return self._id

    def set_handle_name(self, name):
        try:
            Log.info("Setting name to " + name)
            self.handle().name = name
        except AttributeError:
            Log.warn("Skipping " + name)

    def id_updated(self):
        """Update the stored id if the name in ableton has changed"""
        # self._id = self.create_handle_id()
        self.update_hierarchy()

    @classmethod
    def find_wrapper_by_id(cls, wrapperId):
        try:
            return cls._instances[wrapperId]
        except KeyError:
            return None

    def create_handle_id(self):
        """Create a new ID in memory from the handle name"""
        handleName = None
        handleId = None

        # If the wrapper doesn't have a name attr we can skip the split step
        try:
            handleName = self.handle().name
        except AttributeError:
            handleName = PyroWrapper.ID_NULL

        matchedId = PyroWrapper.get_id_from_name(handleName)

        if matchedId:
            handleId = matchedId
        else:
            handleId = PyroWrapper.generate_id()
            handleName = PyroWrapper.generate_id_name_str(handleName, handleId)
            self.defer_action(self.set_handle_name, handleName)
        return handleId

    @staticmethod
    def generate_id():
        PyroWrapper._id_counter += 1
        return str(PyroWrapper._id_counter)

    @staticmethod
    def generate_id_name_str(name, idnum):
        name = name if name else PyroWrapper.ID_NULL
        return name + PyroWrapper.ID_DELIM + str(idnum) + PyroWrapper.ID_END

    @staticmethod
    def get_id_from_name(name):
        """Split a handle name into name and id"""
        idStr = re.search('(?<=' + PyroWrapper.ID_DELIM[0] + '\\' + PyroWrapper.ID_DELIM[1] + ')(.*[^\}])', name)
        return idStr.group(0) if idStr else None

    @staticmethod 
    def get_original_name(name):
        nameStr = re.search('^.*(?=' + PyroWrapper.ID_DELIM[0] + ')', name)
        return nameStr.group(0) if nameStr else name

    def to_object(self, params=None):
        """Converts this wrapper to an object representation"""
        params = params if params else {}

        try:
            name = PyroWrapper.get_original_name(self.handle().name)
        except AttributeError, e:
            name = None

        params.update({
            "id": self.id(),
            "type": self.__class__.__name__,
            "name": name,
            "parent": self.parent().id() if self.parent() else None,
            "index": self.handleindex
        })
        
        return params

class PyroMethodDef:
    def __init__(self, methodname, methodAccess, methodargs=None, callback=None):
        self.methodName = methodname
        self.methodAccess = methodAccess
        self.methodArgs = methodargs if methodargs else {}
        self.callback = callback
