echo "Updating scripts"

LOCAL_SOURCE="$HOME/Code/Showtime-Live"
REMOTE_SOURCE="/Applications/Ableton Live 9 Standard.app/Contents/App-Resources/MIDI Remote Scripts"
LIVE_APP="/Applications/Ableton Live 9 Standard.app/"

rm -R "$REMOTE_SOURCE/FissureVR_Pyro"
mkdir "$REMOTE_SOURCE/FissureVR_Pyro"
cp -R "$LOCAL_SOURCE/" "$REMOTE_SOURCE/FissureVR_Pyro/"

osascript -e 'quit app "Live"'
sleep 0.5

open -a "$LIVE_APP"