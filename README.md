Showtime-Live
-------------

This repository is for a bridge connecting Ableton Live
to a [Showtime](https://github.com/Mystfit/Showtime) network via Pyro remote objects.


Installation
------------

- Install [Showtime](https://github.com/Mystfit/Showtime) for Python.
- Install [Pyro 3.16](https://pypi.python.org/pypi/Pyro)
- Install [python-rtmidi](https://pypi.python.org/pypi/python-rtmidi)

- Copy the contents of Midi_Remote_Scripts to your Remote scripts folder. Ableton have provided some [handy instructions here.](https://www.ableton.com/en/articles/install-third-party-remote-script/)
- Create a Showtime stage. This is done by running the python/Showtime/zst_stage.py script from the Showtime library. (eg. "python zst_stage.py").
- Run LiveShowtimeClient.py and give it the ip:port of the stage. (eg. "python LiveShowtimeClient.py 0.0.0.0:6000" if you're running the stage locally).
- Run Ableton Live and underneath Preferences->Midi select "ShowtimeBridge" from the control surface dropdown, and "LiveShowtime Midi" from the input dropdown.
- You can now run/use any of the test scripts from either the Showtime library or the Showtime-Live library to access Live API features.

Current exposed methods
-----------------------

*Outgoing*
- fired_slot_index
- playing_slot_index
- send_updated
- value_updated

*Incoming*
- fire_clip
    * trackindex
    * clipindex
- play_note
    * note
    * trackindex
    * velocity
    * state (0 = note off, 1 = note on)
- set_send
    * sendindex
    * trackindex
    * value
- set_value
    * category (0 = normal track devices, 1 = return track devices)
    * deviceindex
    * parameterindex
    * value
- stop_track
    * trackindex


*Responders*
 - get_song_layout


Bugs
----

 - This is very much an alpha release, so there are quite a few bugs that are still hanging around and there's plenty of api calls that need to still be exposed from Live. If you restart the LiveShowtime client whilst Live is running, then unloading and reloading the ShowtimeBridge Preferences->Midi->Control Surfaces should refresh the connection.
 - TODO 
