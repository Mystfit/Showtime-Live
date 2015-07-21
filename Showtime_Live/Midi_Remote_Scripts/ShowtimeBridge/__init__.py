try:
    from ShowtimeBridge import ShowtimeBridge
except ImportError:
    pass

# from ShowtimeBridge import ShowtimeBridge

def create_instance(c_instance):
    return ShowtimeBridge(c_instance)
