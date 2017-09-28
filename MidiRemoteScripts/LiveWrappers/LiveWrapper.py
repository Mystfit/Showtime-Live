import re
from ..Logger import Log

from showtime import ZstComponent


class LiveWrapper(ZstComponent):
    # Delimiter for handle name id's in Live
    ID_DELIM = "-{"
    ID_END = "}"
    ID_NULL = "no_name"

    # References to all instances created of this object
    _instances = {}
    _plugs = {}
    _deferred_actions = {}

    # Total ID count
    _id_counter = long(0)

    # Constructor
    def __init__(self, handle, handleindex=None, parent=None):
        self.handleindex = handleindex
        self._handle = handle
        self._parent = parent
        self._children = set()
        self._id = self.create_handle_id()
        self.name = self._id
        if hasattr(self.handle(), "name"):
            self.name = LiveWrapper.get_original_name(self.handle().name)
        if parent:
            if hasattr(self._parent, "add_child"):
                self._parent.add_child(self)
        self.create_listeners()
        if parent:
            ZstComponent.__init__(self, "LiveWrapper", str(self.name), parent)
        else:
            ZstComponent.__init__(self, "LiveWrapper", str(self.name))
        self.activate()
        self.create_plugs()

    # Cleanup
    # -------
    @staticmethod
    def destroy(instance):
        if instance.parent():
            if instance.id() in instance.parent().children():
                instance.parent().children().remove(instance.id())
        for child in instance.children():
            LiveWrapper.destroy(child)
        instance.children().clear()
        instance.destroy_listeners()
        instance.destroy_plugs()
        try:
            del instance.__class__.instances_dict()[instance.id()]
        except KeyError:
            Log.warn("%s missing. Already deleted." % instance.id())

    def create_listeners(self):
        """Create all listeners for this object"""
        if self.handle():
            try:
                self.handle().add_name_listener(self.id_updated)
            except (RuntimeError, AttributeError):
                pass

    def destroy_listeners(self):
        """Destroy all listeners on this wrapper"""
        if self.handle():
            try:
                self.handle().remove_name_listener(self.id_updated)
            except (RuntimeError, AttributeError):
                pass

    def update_hierarchy(self, cls=None, livevector=None):
        """Refreshes the hierarchy of wrappers underneath this wrapper"""
        if cls is not None and livevector is not None:
            parentId = self.parent().id() if self.parent() else None
            cls.remove_child_wrappers(livevector, self.id())
            cls.create_child_wrappers(self, livevector)

    def create_plugs(self):
        pass

    def destroy_plugs(self):
        pass

    def compute(self, plug):
        pass


    # Hierarchy
    # ---------
    def handle(self):
        """Get the Live object reference this wrapper controls"""
        return self._handle

    def parent(self):
        """Get the parent wrapper of this wrapper"""
        return self._parent

    @classmethod
    def create_child_wrappers(cls, parent, livevector):
        """Create missing child wrappers underneath this wrapper"""
        totalNew = 0
        totalExisting = 0
        for index, handle in enumerate(livevector):
            wrappers = cls.find_wrapper_by_handle(handle)
            if len(wrappers):
                totalExisting += len(wrappers)
            else:
                wrapper = cls(handle, index, parent)
                cls.add_instance(wrapper)
                totalNew += 1
                
        if totalNew or totalExisting:
            Log.write("ADDING %s: %s added, %s existing." % (cls.__name__, totalNew, totalExisting))

    @classmethod
    def remove_child_wrappers(cls, livevector, idfilter=None):
        """Remove wrappers that are missing a live object"""

        localInstances = []
        for index, handle in enumerate(livevector):
            # If we receive multiple matching wrappers, we have to
            # make sure we match the right wrapper to the right handle.
            # We can use the handle index as a second identifier
            wrappers = cls.find_wrapper_by_handle(handle)
            for wrapper in wrappers:
                if wrapper:
                    if wrapper.handleindex == index:
                        localInstances.append(wrapper)

        idlist = [w.id() for w in localInstances if w]
        instances = [i for i in cls.instances() if i.parent().id() == idfilter] if idfilter else cls.instances()
        Log.info("Class: %s, Handles: %s, Instances: %s" % (cls.__name__, len(idlist), len(instances)))
        totalRemoved = 0
        for wrapper in instances:
            if wrapper.id() not in idlist:
                Log.info("Destroying wrapper: {0}".format(wrapper.id()))
                LiveWrapper.destroy(wrapper)
                totalRemoved += 1
        if totalRemoved:
            Log.write("REMOVING %s: %s removed." % (cls.__name__, totalRemoved))

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

        # Only update hierarchy when the instrument has been added
        instance.update_hierarchy()
        return instance

    """Returns a list of all instances of this node available"""

    @classmethod
    def instances(cls):
        """Returns a list of all instances of this node available"""
        return cls._instances.values() if cls._instances else []

    @classmethod
    def instances_dict(cls):
        return cls._instances

    @classmethod
    def clear_instances(cls):
        if cls._instances:
            cls._instances.clear()

    @classmethod
    def find_wrapper_by_handle(cls, handle):
        """Find an reference of this class from a given id"""
        name = None
        matching_children = []
        try:
            name = handle.name
        except AttributeError:
            Log.info("Handle %s has no name attr" % handle)
            return matching_children

        handleId = LiveWrapper.get_id_from_name(name)
        if handleId:
            matching_children.append(cls.find_wrapper_by_id(handleId))
        else:
            matching_children = LiveWrapper.find_wrapper_from_handle_parent(handle)
        return matching_children

    @staticmethod
    def find_wrapper_from_handle_parent(handle):
        """Find wrapper for a handle from its siblings"""
        matching_children = []
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
            Log.info("Found parent wrapper. Looking for handle in children. Total children: {0}".format(len(parentWrapper.children())))
            
            for child in parentWrapper.children():
                # We check against name and handle ref due to
                # inconsistencies when comparing Live objects
                try:
                    if child.handle():
                        if child.handle().name == handle.name:
                            Log.info("Found wrapper {0} inside parent. Name:{1}".format(child.id(), child.handle().name))
                            matching_children.append(child)
                except AttributeError:
                    Log.info("Parent handle %s has no name attr" % handle)
        else:
            Log.info("Couldn't find parent wrapper for %s" % parentId)

        return matching_children

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
            Log.warn("Skipping set_handle_name() on " + name)

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
            Log.warn("!!!TODO: Send name change to Showtime stage!!!")
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

    
    # Deferred actions
    # --------
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
