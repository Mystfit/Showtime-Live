import re
from ..Logger import Log

from ..showtime import *
from ..showtime import API as ZST


class LiveWrapper(object):
    # Delimiter for handle name ids in Live
    ID_DELIM = "-{"
    ID_END = "}"
    ID_NULL = "no_name"

    # References to all instances created of this object
    _deferred_actions = {}

    _wrapper_ptrs = dict()
    _ptr_wrappers = dict()


    # Total ID count
    _id_counter = long(0)

    # Constructor
    def __init__(self, name, handle, handle_index=None):
        self.handleindex = handle_index
        self._handle = handle

        # Create Showtime component
        self.component = ZST.ZstComponent(str(name))
        self.component.entity_events().entity_registered.add(self.on_registered)

        # Register Live listeners
        self.create_listeners()

    # Redirect any missing attributes to the Showtime component
    # def __getattr__(self, name):
    #     # Log.write("Looking for attr {} in ZstComponent".format(name))
    #     if hasattr(self.component, name):
    #         return getattr(self.component, name)
    #     raise AttributeError

    def on_registered(self, entity):
        self.create_plugs()

    def __del__(self):
        self.component.entity_events().entity_registered.remove(self.on_registered)

        ZST.ZstComponent.__del__(self)
        self.destroy_listeners()

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

    def id_updated(self):
        pass

    def create_plugs(self):
        pass

    def compute(self, plug):
        pass

    @staticmethod
    def build_name(handle, handle_index):
        raise NotImplementedError("Name builder needs to be implemented by derived class")

    @staticmethod
    def sanitize_name(name):
        return name.replace("/", "-")

    def set_handle_name(self, name):
        try:
            Log.info("Setting name to " + name)
            self.handle().name = name
        except AttributeError:
            Log.warn("Skipping set_handle_name() on " + name)

    # Hierarchy
    # ---------
    def handle(self):
        """Get the Live object reference this wrapper controls"""
        return self._handle

    def refresh_hierarchy(self, postactivate):
        raise NotImplementedError("Refresh hierarchy needs to be implemented in derived wrapper")

    @staticmethod
    def find_wrapper_from_live_ptr(live_ptr):
        result = None
        try:
            result = LiveWrapper._ptr_wrappers[live_ptr]
        except KeyError:
            pass
        return result

    @staticmethod
    def find_live_ptr_from_wrapper(wrapper):
        result = None
        try:
            result = LiveWrapper._wrapper_ptrs[wrapper.URI().path()]
        except KeyError:
            pass
        return result

    @staticmethod
    def update_hierarchy(parent, wrappertype, livevector=None, postactivate=False):
        """Refreshes the hierarchy of wrappers underneath this wrapper"""
        if livevector is not None:
            LiveWrapper.remove_child_wrappers(parent, wrappertype, livevector)
            LiveWrapper.create_child_wrappers(parent, wrappertype, livevector, postactivate)


    @staticmethod
    def create_child_wrappers(parent, wrappertype, livevector, postactivate):
        """Create missing child wrappers underneath this wrapper"""
        totalNew = 0
        totalMissing = 0

        handles_without_wrappers = LiveWrapper.find_handles_missing_entities(wrappertype, livevector, parent)
        totalMissing += len(handles_without_wrappers)

        for index, handle in handles_without_wrappers:

            name = LiveWrapper.sanitize_name(wrappertype.build_name(handle, index))

            # TODO: Find existing entities and rename if our name is a duplicate - move to showtime
            # child_entities = parent.component.get_child_entities()
            # names = [e.URI().last().path() for e in child_entities if e]
            # duplicates = [e for e in names if e.startswith(name)]
            
            # existing_path = ZST.ZstURI("{}/{}".format(parent.URI().path(), name))
            # rename = True if client().find_entity(existing_path) else False
            # if rename:
            #     Log.debug("Found duplicate entities {}".format(",".join([n for n in duplicates])))
            #     orig_name = name
            #     name = "{0}_{1}".format(name, len(duplicates))
            #     Log.debug("Renaming {0} to {1}".format(orig_name, name))

            wrapper = wrappertype(name, handle, index)#.__disown__()
            # if rename:
            #     wrapper.defer_action(wrapper.set_handle_name, name)
            parent.add_child(wrapper.component)

            # Log.debug("Adding {}".format(wrapper.URI().path()))

            # Save memory ID so we can match this wrapper to the handle in the future
            LiveWrapper._wrapper_ptrs[wrapper.component.URI().path()] = handle._live_ptr

            #Save reverse index
            LiveWrapper._ptr_wrappers[handle._live_ptr] = wrapper

            # Add child wrappers, but don't activate them
            wrapper.refresh_hierarchy(False)

            # If we're at the top of the refresh hierarchy, send the root entity
            if postactivate:
                Log.info("Activating {}".format(wrapper.URI().path()))
                ZST.activate_entity_async(wrapper)

            totalNew += 1

        # if totalNew or totalMissing:
        #     Log.debug("Adding {0} instances of {1}".format(totalNew, wrappertype.__name__))

    @staticmethod
    def remove_child_wrappers(parent, wrappertype, livevector):
        """Remove wrappers that are missing a live object"""
        totalRemoved = 0
        removed_entities = LiveWrapper.find_entities_missing_handles(wrappertype, livevector, parent)

        for entity in removed_entities:
            Log.debug("Removing {}".format(entity.URI().path()))
            live_ptr = LiveWrapper.find_live_ptr_from_wrapper(entity)
            del LiveWrapper._ptr_wrappers[live_ptr]
            del LiveWrapper._wrapper_ptrs[entity.URI().path()]
            ZST.deactivate_entity_async(entity)
            totalRemoved += 1

        # if totalRemoved:
        #     Log.debug("Removed {1} instances of {0}.".format(wrappertype.__name__, totalRemoved))

    @staticmethod
    def find_handles_missing_entities(wrappertype, livevector, parent):
        return [(i,h) for i,h in enumerate(livevector) if h._live_ptr not in LiveWrapper._ptr_wrappers]

    @staticmethod
    def find_entities_missing_handles(wrappertype, livevector, parent):
        live_ptrs = [handle._live_ptr for handle in livevector]
        missing = []
        child_entities = None
        try:
            child_entities = parent.get_child_entities()
            for entity in child_entities:
                try:
                    live_ptr =  LiveWrapper.find_live_ptr_from_wrapper(entity)
                    if not live_ptr in live_ptrs:
                        missing.append(entity)
                except KeyError:
                    Log.warn("Couldn't find live ptr for entity {0}".format(entity.URI().path()))
        except AttributeError, e:
            Log.write("find_entities_missing_handles: AttributeError for {}. {}".format(parent, e))

        return missing

    
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
