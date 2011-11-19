from Utils import showMessage

class DBException(Exception):
	def __init__(self, value):
		self.value = value
		showMessage('Error', repr(value))
	
	def __str__(self):
		return repr(self.value)
