try:
    import Showtime_Live.Midi_Remote_Scripts.ShowtimeBridge.Utils as Utils
except ImportError:
    from ShowtimeLive.Utils import Utils

class Log:
    def __init__(self):
        pass

    LOG_INFO = 2
    LOG_WARN = 1
    LOG_ERRORS = 0
    LOG_DEBUG = -1

    titles = {
        LOG_INFO: "Information",
        LOG_WARN: "Warnings",
        LOG_ERRORS: "Errors",
        LOG_DEBUG: "Debug"
    }

    _loggermethod = None
    useNetworkLogging = False
    level = 0

    @staticmethod
    def set_logger(logger):
        Log._loggermethod = logger

    # @staticmethod
    # def set_logger_gui(gui):
    #     Log._loggergui = gui

    @staticmethod
    def log_level_from_name(name):
        for loglevel, logname in Log.titles.iteritems():
            if name == logname:
                return loglevel
        return None

    @staticmethod
    def set_log_level(loglevel):
        Log.level = Utils.Utils.clamp(loglevel, -1, 2)
        Log.write("Setting log level to %s" % Log.titles[loglevel])

    @staticmethod
    def set_log_network(status):
        Log.useNetworkLogging = status
        Log.write("Setting network logging to %s" % status)

    @staticmethod
    def write(message):
        if Log._loggermethod:
            Log._loggermethod(str(message))
        else:
            print(message)

    @staticmethod
    def debug(message):
        # if Log.level >= Log.LOG_DEBUG:
        Log.write("DEBUG: " + str(message))

    @staticmethod
    def info(message):
        if Log.level >= Log.LOG_INFO:
            Log.write("INFO: " + str(message))

    @staticmethod
    def warn(message):
        if Log.level >= Log.LOG_WARN:
            Log.write("WARN: " + str(message))

    @staticmethod
    def error(message):
        if Log.level >= Log.LOG_ERRORS:
            Log.write("ERROR: " + str(message))

    @staticmethod
    def network(message):
        if Log.useNetworkLogging:
            Log.write("NET: " + str(message))
