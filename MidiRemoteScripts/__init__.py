# try:
#     from ShowtimeBridge import ShowtimeBridge
# except ImportError, e:
#     pass
import sys
import os


def create_instance(c_instance):
    try:   
        from ShowtimeBridge import ShowtimeBridge
        return ShowtimeBridge(c_instance)
    except Exception as err:
        from _Framework.ControlSurface import ControlSurface
        bootstrap = ControlSurface(c_instance)
        bootstrap.log_message("Couldn't build Showtime. Falling back to generic ControlSurface for logging")
        bootstrap.log_message(err)

        import traceback
        import os.path
        top = traceback.extract_tb(sys.exc_info()[2])[-1]
        bootstrap.log_message(', '.join([type(err).__name__, os.path.basename(top[0]), str(top[1])]))

        try:
            from ShowtimeBridge import ShowtimeBridge
        except ImportError as e:
            bootstrap.log_message("-----------------------")
            bootstrap.log_message("ShowtimeBridge failed to compile")
            bootstrap.log_message(e)
        return bootstrap
