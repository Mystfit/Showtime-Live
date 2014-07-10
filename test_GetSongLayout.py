import sys
import time
from Showtime.zst_node import *

reader = ZstNode("SongLayout", sys.argv[1])
reader.start()
nodeList = reader.request_node_peerlinks()

print "Nodes on stage:"
print "---------------"
for name, peer in nodeList.iteritems():
    print name, json.dumps(peer.as_dict(), indent=1, sort_keys=True)
print ""

node = nodeList["LiveNode"]
reader.subscribe_to(node)
reader.connect_to_peer(node)

time.sleep(1)

#reader.update_remote_method(node.methods["get_song_layout"], None)
print "Received:" + str(reader.update_remote_method(node.methods["get_song_layout"]).output)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print "Exiting"
    reader.close()
