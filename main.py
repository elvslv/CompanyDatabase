from DB.Db import dbi, User
from sqlalchemy.orm.exc import NoResultFound
from DB.dbExceptions import DBException

class AppUser:
	def __init__(self, login = None, password = None, admin = False):
		self.login = login
		self.password = password
		self.admin = admin

	def getTable(self, tableName):
		for table in dbi.metadata.sorted_tables:
			if table.name == tableName:
				return table

	def getHeaders(self, tableName):
		table = self.getTable(tableName)
		result = []
		for column in table.columns:
			result.append(column.name)
		return result

	def selectAll(self, tableName):
		table = self.getTable(tableName)
		return dbi.query(table).all()

class App:
	instance = None
	curUser = None 

	def __init__(self):
		pass

	def getUser(self, login, password):
		try:
			return dbi.query(User).filter(login == User.login).filter(password == User.password).one()
		except NoResultFound:
			raise DBException("NoResultFound")

	def setCurUser(self, login, password):
		user = self.getUser(login, password)
		self.curUser = AppUser(user.login, user.password, user.admin)

def getAppInstance():
	if App.instance is None:
		App.instance = App()
	return App.instance

appInst = getAppInstance()