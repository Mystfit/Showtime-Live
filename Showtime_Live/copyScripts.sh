echo "Copying Showtime-Live scripts"

LOCAL_SOURCE="$HOME/Code/showtime/Showtime-Live/Showtime_Live/Midi_Remote_Scripts/ShowtimeBridge"
REMOTE_SOURCE="/Applications/Ableton Live 9 Suite.app/Contents/App-Resources/MIDI Remote Scripts/ShowtimeBridge"
LIVE_APP="/Applications/Ableton Live 9 Suite.app/"

rm -R "$REMOTE_SOURCE"
mkdir "$REMOTE_SOURCE"
cd "$LOCAL_SOURCE"
tar cf - --exclude="*.pyc" . | (cd "$REMOTE_SOURCE" && tar xvf - )

osascript -e 'quit app "Live"'
sleep 0.5

open -a "$LIVE_APP"