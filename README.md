Showtime-Live
-------------

This repository is for a bridge connecting Ableton Live
to a [Showtime](https://github.com/Mystfit/Showtime) network via Pyro remote objects.

*Requirements:*
- Requires Python 2.7. 

Installation - All
------------

- Copy the contents of Showtime_Live/Midi_Remote_Scripts to your Remote scripts folder. Ableton have provided some [handy instructions here.](https://www.ableton.com/en/articles/install-third-party-remote-script/)
- Install by using ```python setup.py install```
- From a command window run LiveShowtimeClient.py
- If you're running a seperate Showtime stage node then you can specify the address at the commandline. Run ```LiveShowtimeClient.py --help```
 to list the available commands.
- Start Ableton Live and underneath Preferences->Midi select "ShowtimeBridge" from the control surface dropdown, and "LiveShowtime Midi" (Windows) or your loopMidi port.
- You can now run/use any of the test scripts from either the Showtime library or the Showtime-Live library to access Live API features.

- Create a Showtime stage. This is done by running the python/Showtime/zst_stage.py script from the Showtime library. (eg. "python zst_stage.py").

Installation - Windows
----------------------

Rtmidi-python can't create a virtual midi port on Windows due to limitations in the Windows multimedia api. Instead, use a tool such as [loopmidi](http://www.tobias-erichsen.de/software/loopmidi.html) to create a virtual loopback port. Run the LiveShowtimeClient.py with the flag `--listmidiports` script to print out a list of available midi out ports, then run the script with `-m #` where `#` is the midi port to use.

Current exposed methods
-----------------------

*Outgoing*
- fired_slot_index
- playing_slot_index
- send_updated
- value_updated
- output_meter


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
 - get_tracks


Bugs
----

 - This is very much an alpha release, so there are quite a few bugs that are still hanging around and there's plenty of api calls that need to still be exposed from Live. If you restart the LiveShowtime client whilst Live is running, then unloading and reloading the ShowtimeBridge Preferences->Midi->Control Surfaces should refresh the connection.
 - TODO 
