try:
    from ShowtimeBridge import ShowtimeBridge
except ImportError:
    print("Couldn't import ShowtimeBridge")

def create_instance(c_instance):
    return ShowtimeBridge(c_instance)
