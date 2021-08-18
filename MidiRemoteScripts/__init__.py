import sys
import os

# Live's site-packages folder isn't on the path by default
sys.path.append(os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "Python", "site-packages")))

def create_instance(c_instance):
    try:   
        from ShowtimeLive.ShowtimeBridge import ShowtimeBridge
        return ShowtimeBridge(c_instance)
    except Exception as err:
        from _Framework.ControlSurface import ControlSurface
        bootstrap = ControlSurface(c_instance)
        bootstrap.log_message("Couldn't build Showtime. Falling back to generic ControlSurface for logging")
        bootstrap.log_message(err)
        bootstrap.log_message("Python version: {0}".format(sys.version))
        
        # Print the python traceback
        import traceback
        import os.path
        tb = traceback.extract_tb(sys.exc_info()[2])
        formatted_tb_message = "Traceback:\n"
        for file, line_num, method, line in tb:
            formatted_tb_message += " |- File: {0}\n".format(file)
            formatted_tb_message += " |-- Method: {0}, Line Number: {1}, Line: {2}\n".format(str(method), line_num, line)
        bootstrap.log_message(formatted_tb_message)

        try:
            from ShowtimeLive.ShowtimeBridge import ShowtimeBridge
        except ImportError as e:
            bootstrap.log_message("--------------------------------")
            bootstrap.log_message("ShowtimeBridge failed to compile")
            bootstrap.log_message(e)
        return bootstrap
