#!python

import sys
import Pyro.util
import Pyro.core
from Pyro.errors import NamingError
from optparse import OptionParser

import Showtime_Live.PyroBridge.PyroServerStarter
from Showtime_Live.PyroBridge.LiveRouter import LiveRouter

# Options parser
parser = OptionParser()
parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=True)
parser.add_option("-s", "--stagehost", action="store", dest="stageaddress", type="string", help="IP address of the Showtime stage.", default=None)
parser.add_option("-p", "--stageport", action="store", dest="stageport", type="string", help="Port of the Showtime stage", default="6000")
parser.add_option("-m", "--midiportindex", action="store", dest="midiportindex", type="int", help="Midi loopback port to use. Windows only, make sure loopMidi is running first!", default=1)
parser.add_option("--listmidiports", action="store_true", dest="listmidiports", help="List the available midi ports on the system.", default=False)

(options, args) = parser.parse_args()

if options.listmidiports:
    midiRouter = Showtime_Live.MidiRouter.MidiRouter(None)
    midiRouter.listMidiPorts()
    sys.exit(0)

#Server startup
Showtime_Live.PyroBridge.PyroServerStarter.startServer()

#Event listener
Pyro.core.initClient()

# Set up Pyro/Showtime router
stageaddress = options.stageaddress
if stageaddress:
    stageaddress += ":" + str(options.stageport)

showtimeRouter = LiveRouter(stageaddress, options.midiportindex)

# Enter into the idle loop to handle messages
try:
    showtimeRouter.listen()
except KeyboardInterrupt:
    print "\nExiting..."
    showtimeRouter.close()
