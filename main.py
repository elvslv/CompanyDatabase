from DB.Db import *
from sqlalchemy.orm.exc import NoResultFound
from DB.dbExceptions import DBException
from sqlalchemy import *

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

	def getVisibleHeaders(self, table):
		result = []
		for column in table.columns:
			if not(column.primary_key and column.type is Integer and not column.foreign_keys):
				result.append(column)
		return result

	def selectAll(self, tableName):
		table = self.getTable(tableName)
		return dbi.query(table).all()

	def getRecord(self, tableName, keys):
		table = self.getTable(tableName)
		return dbi.query(table).filter(table[keys[0]['fieldName']] == keys[0]['value']).one()

	def getForeignValues(self, table, field):
		foreignColumn = list(field.foreign_keys)[0].column
		foreignTable = foreignColumn.table
		foreignColumnName = foreignColumn.name

		result = []
		for key, val in dbi.query(field, foreignTable.c[foreignColumnName]).filter(field == 
			foreignTable.c[foreignColumnName]):
			result.append([key, val])

		return result

	def insert(self, table, values):
		obj = tableClasses[table.name]
		tmp = obj(*values)
		dbi.add(tmp)
		dbi.commit()
		
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