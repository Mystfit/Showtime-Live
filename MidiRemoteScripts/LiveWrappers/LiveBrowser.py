from ShowtimeLive.LiveWrapper import LiveWrapper
from ShowtimeLive.Logger import Log


class LiveBrowser(LiveWrapper):

    def __init__(self, name, handle, handleindex):
        LiveWrapper.__init__(self, name, handle, handleindex)
        self.name_writable = False
        self.indexable = False

    @staticmethod
    def build_name(handle, handle_index):
        return "browser"

    def create_listeners(self):
        LiveWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_full_refresh_listener(self.update_hierarchy)

    def destroy_listeners(self):
        LiveWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_full_refresh_listener(self.update_hierarchy)
            except (RuntimeError, AttributeError):
                Log.warn("Couldn't remove browser listener")

    def refresh_hierarchy(self):
        browser_categories = {
            # "sounds": self.handle().sounds,
            # "drums": self.handle().drums,
            "instruments": self.handle().instruments
            # "audio_effects": self.handle().audio_effects,
            # "midi_effects": self.handle().midi_effects,
            # "max_for_live": self.handle().max_for_live,
            # "plugins": self.handle().plugins,
            # "clips": self.handle().clips,
            # "samples": self.handle().samples
        }

        browser_places = {
            "packs": self.handle().packs,
            "user_library": self.handle().user_library,
            "current_project": self.handle().current_project
        }

        flattened_browser = {}
        for category, item in browser_categories.iteritems():
            flattened_browser.update(self.all_loadable_children_in_item(item))

        for uri, item in flattened_browser.iteritems():
            Log.info("URI is {0}: Name is:{1} Is device:{2}".format(uri, item.name, item.is_device))

    def all_loadable_children_in_item(self, browser_item):
        children = {}
        if browser_item:
            if not browser_item.is_folder and browser_item.is_loadable:
                children[browser_item.uri] = browser_item
        if hasattr(browser_item, "children"):
            for child in browser_item.children:
                children.update(self.all_loadable_children_in_item(child))
        return children
