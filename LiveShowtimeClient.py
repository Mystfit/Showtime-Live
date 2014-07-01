import sys
import Pyro.util
import Pyro.core
from Pyro.errors import NamingError

import PyroBridge.PyroServerStarter
from PyroBridge.ShowtimeRouter import ShowtimeRouter


if len(sys.argv) < 2:
    print "Need a ZST stage address."
    sys.exit(0)

#Server startup
PyroBridge.PyroServerStarter.startServer()

#Event listener
Pyro.core.initClient()

# Set up Pyro/Showtime router
showtimeRouter = ShowtimeRouter(sys.argv[1])

# Enter into the idle loop to handle messages
try:
    showtimeRouter.listen()
except KeyboardInterrupt:
    print "\nExiting..."
    showtimeRouter.close()
