import itertools
import Live
from ShowtimeLive.LiveWrappers.LiveWrapper import LiveWrapper
from ShowtimeLive.LiveWrappers.LiveTrack import LiveTrack
from ShowtimeLive.showtimeAPI import API as ZST
from ShowtimeLive.Utils import Utils
from ShowtimeLive.Logger import Log
import ShowtimeLive.showtimeAPI as showtime
import xml.etree.ElementTree as ET

class LiveSong(LiveWrapper):
    def __init__(self, name, handle):
        LiveWrapper.__init__(self, name, handle, 0)
        self.returns = ZST.ZstComponent("returns")
        self.tracks = ZST.ZstComponent("tracks")
        showtime.client().register_entity(self.returns)
        showtime.client().register_entity(self.tracks)

    def on_registered(self, entity):
        Log.write("Song registered")
        LiveWrapper.on_registered(self, entity)
        self.component.add_child(self.returns)
        self.component.add_child(self.tracks)


    @staticmethod
    def build_name(handle, handle_index):
        return "song"

    # -------------------
    # Wrapper definitions
    # -------------------
    def create_listeners(self):
        LiveWrapper.create_listeners(self)
        if self.handle():
            self.handle().add_current_song_time_listener(self.song_time_updated)
            self.handle().add_tracks_listener(self.refresh_tracks)
            self.handle().add_return_tracks_listener(self.refresh_returns)
        else:
            Log.write("No song handle")

    def destroy_listeners(self):
        LiveWrapper.destroy_listeners(self)
        if self.handle():
            try:
                self.handle().remove_current_song_time_listener(self.song_time_updated)
                self.handle().remove_tracks_listener(self.refresh_tracks)
                self.handle().remove_return_tracks_listener(self.refresh_returns)
            except (RuntimeError, AttributeError):
                Log.warn("Couldn't remove device listener")

    # --------
    # Outgoing
    # --------
    def song_time_updated(self):
        self.tick()
        meterLevels = {}
        for track_handle in self.handle().tracks:
            track = LiveWrapper.find_wrapper_from_live_ptr(track_handle._live_ptr)
            if track:
                if track.handle().has_midi_output:
                    Utils.truncate_float(track.handle().output_meter_level, 4)
                else:
                    meterLevels[track.URI().path()] = Utils.truncate_float(((track.handle().output_meter_left + track.handle().output_meter_right) * 0.5), 4)

    # ---------
    # Hierarchy
    # ---------

    def refresh_tracks(self, postactivate=True):
        Log.info("{0} - Track list changed".format(self.component.URI().last().path()))
        LiveWrapper.update_hierarchy(self.tracks, LiveTrack, self.handle().tracks, postactivate)

    def refresh_returns(self, postactivate=True):
        Log.info("{0} - Returns list changed".format(self.component.URI().last().path()))
        LiveWrapper.update_hierarchy(self.returns, LiveTrack, self.handle().return_tracks, postactivate)

    def refresh_hierarchy(self, postactivate):
        self.refresh_tracks(postactivate)
        self.refresh_returns(postactivate)

        # Master track always exists and remember to register it
        LiveWrapper.update_hierarchy(self.component, LiveTrack, [self.handle().master_track], postactivate)

    # ---------
    # Utilities
    # ---------
    def tick(self):
        for track_handle in self.handle().tracks:
            track = LiveWrapper.find_wrapper_from_live_ptr(track_handle._live_ptr)
            if track:
                track.tick()


    def toXMLElement(self):
        # Build top level nodes
        project_node = ET.Element("project", {"version": "0.1"})
        version = "{}.{}.{}".format(Live.Application.get_application().get_major_version(), Live.Application.get_application().get_minor_version(), Live.Application.get_application().get_bugfix_version())
        application_node = ET.SubElement(project_node, "application", {"Ableton Live": version})
        tracks_node = ET.SubElement(project_node, "tracks")
        arrangement_node = ET.SubElement(project_node, 'arrangement', {"id": "arrangement"})
        lanes_node = ET.SubElement(arrangement_node, 'lanes', {"timebase": "beats", "id": "lanes"})
        scenes_node = ET.SubElement(project_node, "scenes")

        # Serialize scenes
        tracks = []
        for t in self.handle().tracks:
            tracks.append(t)
        for r in self.handle().return_tracks:
            tracks.append(r)
        tracks.append(self.handle().master_track)

        for track in tracks:
            track_wrapper = LiveWrapper.find_wrapper_from_live_ptr(track._live_ptr)
            track_node, lane_node = track_wrapper.toXMLElement() if track_wrapper else (None, None)
            tracks_node.append(track_node)
            lanes_node.append(lane_node)

        return project_node
        # return ET.Element("lanes", {"timebase": beats})
