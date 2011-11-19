from DB.Db import *
from sqlalchemy.orm.exc import NoResultFound
from DB.dbExceptions import DBException
from sqlalchemy import *

class AppUser:
	def __init__(self, login = None, password = None, admin = False):
		self.login = login
		self.password = password
		self.admin = admin

	def canUpdate(self, tableName):
		return True

	def getTable(self, tableName):
		return appInst.getTable(tableName)

	def getHeaders(self, tableName):
		return appInst.getHeaders(tableName)

	def getVisibleHeaders(self, table):
		return appInst.getVisibleHeaders(table)

	def selectAll(self, tableName):
		return appInst.selectAll(tableName)

	def getRecord(self, tableName, keys):
		return appInst.getRecord(tableName, keys)

	def getForeignValues(self, table, field):
		return appInst.getForeignValues(table, field)

	def insert(self, table, values):
		return appInst.insert(table, values)
	
class App:
	instance = None
	curUser = None 

	def __init__(self):
		pass

	def getUser(self, login, password, msg = None):
		try:
			return dbi.query(User).filter(login == User.login).filter(password == User.password).one()
		except NoResultFound:
			raise DBException(msg if msg else "NoResultFound")

	def setCurUser(self, login, password):
		user = self.getUser(login, password)
		self.curUser = AppUser(user.login, user.password, user.admin)

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

	def getHeadersWithForeignValues(self, tableName):
		table = self.getTable(tableName)
		columns = []
		for column in table.columns:
			columns.append(self.getColumnName(column))
		return columns

	def getVisibleHeaders(self, table):
		result = []
		for column in table.columns:
			if not(column.primary_key and isinstance(column.type, Integer) and not column.foreign_keys):
				result.append(column)
		return result

	def getColumnName(self, column):
		if column.foreign_keys:
			col = list(column.foreign_keys)[0].column
			return col.table.name if col.name == 'id' else col.name
		else:
			return column.name
	
	def selectAll(self, tableName):
		table = self.getTable(tableName)
		return dbi.query(table).all()

	def selectAllWithForeignValues(self, tableName):
		table = self.getTable(tableName)
		columns = []
		filterStmts = dict()
		for column in table.columns:
			if column.foreign_keys:
				foreignColumn = list(column.foreign_keys)[0].column
				filterStmts[column] = foreignColumn
				if foreignColumn.name == 'id':
					foreignColumn = foreignColumn.table.c['name']
				columns.append(foreignColumn)
			else:
				columns.append(column)
		q = dbi.query(*columns)
		for attr, value in filterStmts.items():
			q = q.filter(attr == value)
		return q.all()

	def getRecord(self, tableName, keys):
		table = self.getTable(tableName)
		return dbi.query(table).filter(table[keys[0]['fieldName']] == keys[0]['value']).one()

	def getForeignValues(self, table, field):
		foreignColumn = list(field.foreign_keys)[0].column
		foreignTable = foreignColumn.table
		foreignColumnName = foreignColumn.name
		columnWithName = 'name' if foreignColumnName == 'id' else foreignColumnName

		result = []
		q = dbi.query(foreignTable.c[foreignColumnName], foreignTable.c[columnWithName]).all()
		for key, val in q:
			result.append([key, val])

		return result	

	def insert(self, table, values):
		obj = tableClasses[table.name]
		tmp = obj(*values)
		dbi.add(tmp)

	def addUser(self, username, password, isAdmin):
		dbi.addUnique(User(username, password, isAdmin), 'User with the same login already exists')

	def addCompany(self, name, details):
		dbi.addUnique(Company(name, details), 'Company with the same name already exists') 

	def admins(self):
		result = dbi.query(User).filter(User.admin == True).all()
		return result

def getAppInstance():
	if App.instance is None:
		App.instance = App()
	return App.instance

appInst = getAppInstance()
