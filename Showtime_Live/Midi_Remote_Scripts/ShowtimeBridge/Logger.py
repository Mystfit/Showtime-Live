class Log():
    LOG_INFO = 2
    LOG_WARN = 1
    LOG_ERRORS = 0
    LOG_DEBUG = -1

    _loggermethod = None
    _loggerlevel = 0
    _networklogging = False

    @staticmethod
    def set_logger(logger):
        Log._loggermethod = logger

    @staticmethod
    def set_log_level(level):
        Log._loggerlevel = level
    
    @staticmethod
    def set_log_network(status):
        Log._networklogging = status

    @staticmethod
    def write(message):
        if Log._loggermethod:
            Log._loggermethod(str(message))
        else:
            print(message)

    @staticmethod
    def debug(message):
        # if Log._loggerlevel >= Log.LOG_DEBUG:
        Log.write("DEBUG: " + str(message))

    @staticmethod
    def info(message):
        if Log._loggerlevel >= Log.LOG_INFO:
            Log.write("INFO: " + str(message))

    @staticmethod
    def warn(message):
        if Log._loggerlevel >= Log.LOG_WARN:
            Log.write("WARN: " + str(message))

    @staticmethod
    def error(message):
        if Log._loggerlevel >= Log.LOG_ERRORS:
            Log.write("ERROR: " + str(message))

    @staticmethod
    def network(message):
        if Log._networklogging:
            Log.write("NET: " + str(message))
