try:
	from ShowtimeBridge import ShowtimeBridge
except ImportError:
	pass


def create_instance(c_instance):
    return ShowtimeBridge(c_instance)
