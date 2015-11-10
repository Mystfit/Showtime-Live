Showtime-Live
-------------

This repository is for a bridge connecting Ableton Live
to a [Showtime](https://github.com/Mystfit/Showtime) network.

*Requirements:*
- Requires Python 2.7. [Get it here.](https://www.python.org/downloads/release/python-2710/) 

Installation - All
------------

- Install using ```python setup.py install```
- If you have Ableton Live installed in a non-default location, then copy the contents of Showtime_Live/Midi_Remote_Scripts to your Ableton Live Midi Remote Script directoy. Ableton have provided some [handy instructions here.](https://www.ableton.com/en/articles/install-third-party-remote-script/)
- From a command prompt or terminal run `LiveShowtimeClient.py`. it is installed as a script, so should be callable globally. If you are on Windows, you can locate the script in [Python_Install_Directory]/Scripts/LiveShowtimeClient.py
- If you're running a seperate Showtime stage node then you can specify its address at runtime. Use ```LiveShowtimeClient.py --help```
 to list the available commands.
- Start Ableton Live and underneath Preferences/Options->Midi select "ShowtimeBridge" from the control surface dropdown, and "LiveShowtime Midi" or your loopMidi port (Windows only).


Installation - Windows
----------------------

Rtmidi-python can't create a virtual midi port on Windows due to limitations in the Windows multimedia api. Instead, use a tool such as [loopmidi](http://www.tobias-erichsen.de/software/loopmidi.html) to create a virtual loopback port. Run the LiveShowtimeClient.py with the flag `--listmidiports` to print out a list of available midi out ports, then run the script with `-m #` where `#` is the midi port to use.
IMPORTANT - Currently the --listmidiports command will crash. If you are using LoopMidi then try using numbers starting from 0 and increasing until the LoopMidi application shows a constant stream of data flowing through it. I've had the most success with midi index 1.

Current exposed methods
-----------------------

Troubleshooting
----
 - This is very much an alpha release, so there are quite a few bugs that are still hanging around and there's plenty of api calls that need to still be exposed from Live. If you restart the LiveShowtime client whilst Live is running, then unloading and reloading the ShowtimeBridge Preferences->Midi->Control Surfaces will refresh the connection.