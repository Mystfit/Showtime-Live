from PyroWrapper import *
from PyroClip import PyroClip
from ..Utils import Utils


class PyroClipslot(PyroWrapper):
    
    # -------------------
    # Wrapper definitions
    # -------------------
    def create_listeners(self):
        PyroWrapper.create_listeners(self)
        if self.handle():
        	self.handle().add_has_clip_listener(self.update_hierarchy)
        	self.handle().add_is_triggered_listener(self.clip_status)
            self.handle().add_playing_status_listener(self.clip_status)

    def destroy_listeners(self):
        PyroWrapper.destroy_listeners(self)
        if self.handle():
            try:
	        	self.handle().remove_has_clip_listener(self.update_hierarchy)
	        	self.handle().remove_is_triggered_listener(self.clip_status)
            	self.handle().remove_playing_status_listener(self.clip_status)
            except RuntimeError:
                Log.warn("Couldn't remove clipslot listeners")

    @classmethod
    def register_methods(cls):
        pass

    def update_hierarchy(self):
    	clip = []
    	if self.handle().clip:
    		clip.append(self.handle().clip)
        PyroWrapper.update_hierarchy(self, PyroClip, clip)

    # --------
    # Outgoing
    # --------
    def clip_status(self):
    	for clip in self.children():
        	clip.update(PyroClip.CLIP_STATUS, {"status": self.handle().playing_status})

    # --------
    # Incoming
    # --------

    # ---------
    # Utilities
    # ---------