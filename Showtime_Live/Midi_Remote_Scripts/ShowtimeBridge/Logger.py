class Log():
	_loggermethod = None

	@staticmethod
	def set_logger(logger):
		Log._loggermethod = logger

	@staticmethod
	def write(message):
		if Log._loggermethod:
			Log._loggermethod(str(message))
		else:
			print(message)