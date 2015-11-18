try:
    from ShowtimeBridge import ShowtimeBridge
except ImportError, e:
    pass

def create_instance(c_instance):
    try:
        return ShowtimeBridge(c_instance)
    except NameError:
        from _Framework.ControlSurface import ControlSurface
        bootstrap = ControlSurface(c_instance)
        try:
            from ShowtimeBridge import ShowtimeBridge
        except ImportError, e:
            bootstrap.log_message("-----------------------")
            bootstrap.log_message("ShowtimeBridge failed to compile")
            bootstrap.log_message(e)
        return bootstrap
