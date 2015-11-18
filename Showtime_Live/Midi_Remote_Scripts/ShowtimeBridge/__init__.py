# try:
#     from ShowtimeBridge import ShowtimeBridge
# except ImportError, e:
#     pass

def create_instance(c_instance):
    try:
        from ShowtimeBridge import ShowtimeBridge
        return ShowtimeBridge(c_instance)
    except Exception, err:
        from _Framework.ControlSurface import ControlSurface
        bootstrap = ControlSurface(c_instance)
        bootstrap.log_message("Couldn't build Showtime. Falling back to generic ControlSurface for logging")
        bootstrap.log_message(err)
        try:
            from ShowtimeBridge import ShowtimeBridge
        except ImportError, e:
            bootstrap.log_message("-----------------------")
            bootstrap.log_message("ShowtimeBridge failed to compile")
            bootstrap.log_message(e)
        return bootstrap
