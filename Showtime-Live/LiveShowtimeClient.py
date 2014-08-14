import sys
import Pyro.util
import Pyro.core
from Pyro.errors import NamingError

import PyroBridge.PyroServerStarter
from PyroBridge.ShowtimeRouter import ShowtimeRouter

#Server startup
PyroBridge.PyroServerStarter.startServer()

#Event listener
Pyro.core.initClient()

# Set up Pyro/Showtime router
stageAddress = None
if(len(sys.argv) > 1):
	stageAddress = sys.argv[1]
showtimeRouter = ShowtimeRouter(stageAddress)

# Enter into the idle loop to handle messages
try:
    showtimeRouter.listen()
except KeyboardInterrupt:
    print "\nExiting..."
    showtimeRouter.close()
