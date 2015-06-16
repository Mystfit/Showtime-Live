echo "Copying Showtime-Live scripts"

LOCAL_SOURCE="$HOME/Code/showtime/Showtime-Live/Showtime_Live/Midi_Remote_Scripts/ShowtimeBridge"
REMOTE_SOURCE="/Applications/Ableton Live 9 Suite.app/Contents/App-Resources/MIDI Remote Scripts"
LIVE_APP="/Applications/Ableton Live 9 Suite.app/"

rm -R "$REMOTE_SOURCE/ShowtimeBridge"
mkdir "$REMOTE_SOURCE/ShowtimeBridge"
cp -R "$LOCAL_SOURCE/" "$REMOTE_SOURCE/ShowtimeBridge/"

osascript -e 'quit app "Live"'
sleep 0.5

open -a "$LIVE_APP"