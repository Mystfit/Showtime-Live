import showtime.showtime as ZST
import time, math

raw_input("Attach debugger now then press a key")

client = ZST.ShowtimeClient()
client.init("cli", True)
client.auto_join_by_name("stage")

a = ZST.ZstComponent("a")
client.get_root().add_child(a)
out = ZST.ZstOutputPlug("out", ZST.ZstValueType_FloatList)
a.add_child(out)
client.poll_once()
assert out.can_fire()

in_ent = client.find_entity(ZST.ZstURI("LiveBridge/song/returns/B-Delay/devices/Delay/parameters/Dry-Wet/in"))
input_plug = ZST.cast_to_input_plug(in_ent)
client.connect_cable(input_plug, out)
time.sleep(0.1)

#raw_input("Press any key to exit")

count = 0.0
try:
	while True:
		out.append_float(math.sin(count) * 0.5 + 0.5)
		out.fire()
		time.sleep(0.01)
		count += 0.1

except KeyboardInterrupt:
	pass

client.destroy()