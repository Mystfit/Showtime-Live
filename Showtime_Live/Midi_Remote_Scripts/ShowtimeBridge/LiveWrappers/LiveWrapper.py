import re
from ..Logger import Log


class LiveWrapper(object):
    # Proxy method types for Showtime
    METHOD_READ = "read"
    METHOD_WRITE = "write"
    METHOD_RESPOND = "responder"

    # Delimiter for handle name id's in Live
    ID_DELIM = "-{"
    ID_END = "}"
    ID_NULL = "no_name"

    LAYOUT_ADDED = "added"
    LAYOUT_REMOVE = "removed"
    LAYOUT_UPDATED = "layout_updated"

    # Class method references
    _incoming_methods = {}
    _outgoing_methods = {}

    # References to all instances created of this object
    _instances = {}

    # Publisher for all wrappers
    _publisher = None

    # Queued wrapper events
    _deferred_actions = {}
    _layout_updates = []

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
        self.update_hierarchy()
        self.create_listeners()

    # Cleanup
    # -------
    @staticmethod
    def destroy(instance):
        """Destroy a wrapper"""
        LiveWrapper.queue_layout_diff({
            "status": LiveWrapper.LAYOUT_REMOVE,
            "id": instance.id()
        })

        if instance.parent():
            if instance.id() in instance.parent().children():
                instance.parent().children().remove(instance.id())
        for child in instance._children:
            LiveWrapper.destroy(child)
        instance._children.clear()
        instance.destroy_listeners()
        try:
            del instance.__class__._instances[instance.id()]
        except KeyError:
            Log.warn("%s missing. Already deleted." % instance.id())
        
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
        if cls is not None and livevector is not None:
            parentId = self.parent().id() if self.parent() else None
            cls.remove_child_wrappers(livevector, self.id())
            cls.create_child_wrappers(self, livevector)

    @classmethod
    def create_child_wrappers(cls, parent, livevector):
        """Create missing child wrappers underneath this wrapper"""
        totalNew = 0
        totalExisting = 0
        for index, handle in enumerate(livevector):
            wrapper = cls.find_wrapper_by_handle(handle)
            if not wrapper:
                cls.add_instance(cls(handle, index, parent))
                totalNew += 1
            else:
                totalExisting += 1
        Log.info("ADDING %s: %s added, %s existing." % (cls.__name__, totalNew, totalExisting))


    @classmethod
    def remove_child_wrappers(cls, livevector, idfilter=None):
        """Remove wrappers that are missing a live object"""
        localInstances = [cls.find_wrapper_by_handle(handle) for handle in livevector]
        idlist = [w.id() for w in localInstances if w]
        instances = [i for i in cls.instances() if i.parent().id() == idfilter] if idfilter else cls.instances()
        Log.info("Class: %s, Handles: %s, Instances: %s" % (cls.__name__, len(idlist), len(instances)))
        totalRemoved = 0
        for wrapper in instances:
            if wrapper.id() not in idlist:
                totalRemoved += 1
                LiveWrapper.destroy(wrapper)
        Log.info("REMOVING %s: %s removed." % (cls.__name__, totalRemoved))

    
    def add_child(self, child):
        """Add a child wrapper to this wrapper"""
        self._children.add(child)
    
    def children(self):
        """Return all children of this wrapper"""
        return self._children


    # Class instances
    # ---------------
    @classmethod
    def add_instance(cls, instance):
        """Registers an instance of the class at the class level"""
        if not cls._instances:
            cls._instances = {}
        cls._instances[instance.id()] = instance

        diff_status = {"status": LiveWrapper.LAYOUT_ADDED} 
        diff_status.update(instance.to_object())
        LiveWrapper.queue_layout_diff(diff_status)

        return instance

    """Returns a list of all instances of this node available"""
    @classmethod
    def instances(cls):
        """Returns a list of all instances of this node available"""
        return cls._instances.values() if cls._instances else []

    @classmethod
    def clear_instances(cls):
        if cls._instances:
            cls._instances.clear()

    @classmethod
    def find_wrapper_by_handle(cls, handle):
        """Find an reference of this class from a given id"""
        name = None
        try:
            name = handle.name
        except AttributeError:
            Log.info("Handle %s has no name attr" % handle)
            return None

        handleId = LiveWrapper.get_id_from_name(name)
        if handleId:
            return cls.find_wrapper_by_id(handleId)
        else:
            Log.info("No id in name. Searching in parent")
            return LiveWrapper.find_wrapper_from_handle_parent(handle)
        return None

    @staticmethod
    def find_wrapper_from_handle_parent(handle):
        '''Find wrapper for a handle from its siblings'''
        parentId = None
        try:
            parentId = LiveWrapper.get_id_from_name(handle.canonical_parent.name)
        except AttributeError:
            Log.info("Parent has no name. Handle is %s" % handle.canonical_parent)
        
        parentWrapper = None
        for cls in LiveWrapper.__subclasses__():
            parentWrapper = cls.find_wrapper_by_id(parentId)
            if parentWrapper:
                break
        if parentWrapper:
            for child in parentWrapper.children():
                # We check against name and handle ref due to
                # inconsistencies when comparing Live objects
                try:
                    if child.handle():
                        if child.handle().name == handle.name:
                            Log.info("Found wrapper inside parent. %s" % child.handle().name)
                            return child
                except AttributeError:
                    Log.info("Parent handle %s has no name attr" % handle)
        else:
            Log.info("Couldn't find parent wrapper for %s" % parentId)
        return None

    @classmethod
    def add_outgoing_method(cls, methodname):
        """Registers a method for this wrapper that will publish to the network"""
        if methodname in cls._outgoing_methods:
            Log.warn("Outgoing method aready exists")
            return

        cls._outgoing_methods[methodname] = PyroMethodDef(methodname, LiveWrapper.METHOD_READ)

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

        accessType = LiveWrapper.METHOD_RESPOND if isResponder else LiveWrapper.METHOD_WRITE
        cls._incoming_methods[methodname] = PyroMethodDef(methodname, accessType, methodargkeys, callback)


    # Network
    # -------
    @staticmethod
    def set_publisher(publisher):
        """Set the global publisher for all wrappers"""
        LiveWrapper._publisher = publisher

    @staticmethod
    def register_methods():
        """
        Register base methods for all classes.
        Subclasses can override this to add their own methods
        """
        LiveWrapper.add_outgoing_method(LiveWrapper.LAYOUT_UPDATED)

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
        if len(LiveWrapper._deferred_actions.keys()) > 0:
            for callback, action in LiveWrapper._deferred_actions.iteritems():
                try:
                    callback(action[1])
                except Exception, e:
                    Log.error("Couldn't run deferred action. %s" % e)
            LiveWrapper._deferred_actions.clear()

    def defer_action(self, method, argument):
        LiveWrapper._deferred_actions[method] = (self, argument)

    def update(self, action, values=None):
        """Send the updated wrapper value to the network"""
        val = {"value": values, "id": self.id()}
        LiveWrapper._publisher.send_to_showtime(action, val)

    def respond(self, action, values):
        """Send the updated wrapper value to the network""" 
        val = {"value": values, "id": self.id()}
        LiveWrapper._publisher.send_to_showtime(action, val, True)


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
        self.update_hierarchy()

    @classmethod
    def find_wrapper_by_id(cls, wrapperId):
        try:
            return cls._instances[wrapperId]
        except KeyError:
            pass

        return None

    def create_handle_id(self):
        """Create a new ID in memory from the handle name"""
        handleName = None
        handleId = None

        # If the wrapper doesn't have a name attr we can skip the split step
        try:
            handleName = self.handle().name
        except AttributeError:
            handleName = LiveWrapper.ID_NULL

        matchedId = LiveWrapper.get_id_from_name(handleName)

        if matchedId:
            handleId = matchedId
        else:
            handleId = LiveWrapper.generate_id()
            handleName = LiveWrapper.generate_id_name_str(handleName, handleId)
            self.defer_action(self.set_handle_name, handleName)
        return handleId

    @staticmethod
    def generate_id():
        LiveWrapper._id_counter += 1
        return str(LiveWrapper._id_counter)

    @staticmethod
    def generate_id_name_str(name, idnum):
        name = name if name else LiveWrapper.ID_NULL
        return name + LiveWrapper.ID_DELIM + str(idnum) + LiveWrapper.ID_END

    @staticmethod
    def get_id_from_name(name):
        """Split a handle name into name and id"""
        idStr = re.search('(?<=' + LiveWrapper.ID_DELIM[0] + '\\' + LiveWrapper.ID_DELIM[1] + ')(.*[^\}])', name)
        return idStr.group(0) if idStr else None

    @staticmethod 
    def get_original_name(name):
        nameStr = re.search('^.*(?=' + LiveWrapper.ID_DELIM[0] + ')', name)
        return nameStr.group(0) if nameStr else name

    def to_object(self, params=None):
        """Converts this wrapper to an object representation"""
        params = params if params else {}

        try:
            name = LiveWrapper.get_original_name(self.handle().name)
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

    @staticmethod
    def queue_layout_diff(diffItem):
        LiveWrapper._layout_updates.append(diffItem)
        LiveWrapper._deferred_actions[LiveWrapper.send_layout_diff] = (None, None)

    @staticmethod
    def send_layout_diff(args):
        LiveWrapper._publisher.send_to_showtime(LiveWrapper.LAYOUT_UPDATED, {"val": LiveWrapper._layout_updates})
        LiveWrapper._layout_updates[:] = []


class PyroMethodDef:
    def __init__(self, methodname, methodAccess, methodargs=None, callback=None):
        self.methodName = methodname
        self.methodAccess = methodAccess
        self.methodArgs = methodargs if methodargs else {}
        self.callback = callback
