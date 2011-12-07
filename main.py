from PyQt4 import QtGui, QtCore
from DB.Db import *
from sqlalchemy.orm.exc import NoResultFound
from DB.dbExceptions import DBException
from sqlalchemy import *
from sqlalchemy.sql import *
from Utils import *
import math

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
		
	def update(self, table, keys, values):
		return appInst.update(table, keys, values)

	def delete(self, table, keys):
		return appInst.delete(table, keys)

class App:
	instance = None
	curUser = None 
	
	def __init__(self):
		self.tables = list()

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
			result.append(column)
		return result

	def isVisible(self, column):
		return not(column.primary_key and isinstance(column.type, Integer) and\
			not column.foreign_keys)

	def getHeadersWithForeignValues(self, tableName):
		table = self.getTable(tableName)
		columns = []
		for column in table.columns:
			if self.isVisible(column):
				columns.append(self.getColumnName(column))
		return columns

	def getVisibleHeaders(self, table):
		result = []
		for column in table.columns:
			if self.isVisible(column):
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

	def selectAllWithForeignValues(self, tableName, isReport = None):
		table = self.getTable(tableName)
		columns = []
		filterStmts = dict()
		for column in table.columns:
			if not(self.isVisible(column)):
				continue
			if column.foreign_keys:
				foreignColumn = list(column.foreign_keys)[0].column
				filterStmts[column] = foreignColumn
				if foreignColumn.name == 'id':
					foreignColumn = foreignColumn.table.c['name']
				columns.append(foreignColumn)
			else:
				columns.append(column)
		if tableName == 'tasksDependencies':
			q = dbi.session.execute('''select a.name, b.name from tasks as a, 
				tasks as b, tasksDependencies as c
				where a.id = c.masterId and b.id = c.slaveId''').fetchall()
			return q
		elif tableName == 'jobs' and isReport:
			q = dbi.session.execute('''select c.name, b.name, a.description, 
				a.completionDate - a.startDate from jobs as a, tasks as b, 
				employees as c where a.employeeId = c.id and b.id =a.taskId''').fetchall()
			return q
		q = dbi.query(*columns)
		for attr, value in filterStmts.items():
			q = q.filter(attr == value)
		return q.all()

	def getRecord(self, tableName, keys):
		table = self.getTable(tableName)
		query = dbi.query(*self.getVisibleHeaders(table))
		for key in keys:
			query = query.filter(table.c[key['name']] == key['value'])
		return query.one()

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
		vals = [value['value'] for value in values]
		tmp = obj(*vals)
		dbi.addUnique(tmp)

	def update(self, table, keys, values):
		table = tableClasses[table.name]
		obj = dbi.query(table)
		for key in keys:
			obj = obj.filter(getattr(table, key['name']) == key['value'])
		obj.update(values)

	def delete(self, table, keys):
		table = tableClasses[table]
		obj = dbi.query(table)
		for key in keys:
			obj = obj.filter(getattr(table, key['name']) == key['value'])
		obj.delete()

	def updateTableViews(self):
		for table in self.tables:
			table.fillCells()

	def addUser(self, username, password, isAdmin):
		dbi.addUnique(User(username, password, isAdmin), 'User with the same login already exists')

	def addCompany(self, name, details):
		newCompany = Company(name, details)
		if not len(self.admins):
			self.company = newCompany
		dbi.addUnique(newCompany, 'Company with the same name already exists') 

	def getAdmins(self):
		self.admins = dbi.query(User).filter(User.admin == True).all()
		return self.admins

	def hasProjects(self):
		return len(dbi.query(Project).all())

	def hasPartners(self):
		return len(dbi.query(Company).all()) > 1

	def getTasksNumOnProject(self, projectId):
		project = dbi.query(Project).filter(Project.id == projectId).one()
		return len(project.tasks)

	def getMaxTasksNumOnProjects(self):
		tasksOnProject = dbi.query(func.count(Task.id)).group_by(Task.projectId).all()
		maxi = 0
		for tasks in tasksOnProject:
			if tasks > maxi:
				maxi = tasks
		return maxi

	def getMaxTasksNumOnProjectsWithManager(self):
		if not self.curUser:
			return 0
		projects = dbi.query(ProjectEmployee.projectId).filter(ProjectEmployee.employeeId == 
			self.getEmployee().id).filter(ProjectEmployee.role == ROLE_MANAGER).all()
		maxi = 0
		for project in projects:
			m = self.getTasksNumOnProject(project.id)
			if m > maxi:
				maxi = m
		return maxi

	def getProjectByTask(self, taskId):
		return dbi.query(Task).filter(taskId == Task.id).one().project

	def getTasksDependencyGraph(self):
		query = dbi.query(TasksDependency.slaveId, 
			TasksDependency.masterId).group_by(TasksDependency.slaveId).all()
		maxId = dbi.query(func.max(TasksDependency.slaveId)).scalar()
		maxTaskId = dbi.query(func.max(Task.id)).scalar()
		graph = [[] for i in range(maxId + 1)]
		for q in query:
			graph[q[0]].append(q[1])
		return graph, maxTaskId

	def isAdmin(self):
		return self.curUser and self.curUser.admin

	def getLogin(self):
		return self.curUser.login if self.curUser else None

	def getEmployee(self):
		return dbi.query(User).filter(self.curUser.login == 
			User.login).filter(self.curUser.password == User.password).one() if self.curUser else None
		
	def isManager(self):
		empl = self.getEmployee()
		if not empl:
			return False
		return len(dbi.query(ProjectEmployee).filter(ProjectEmployee.employeeId == 
			empl.id).filter(ProjectEmployee.role == ROLE_MANAGER).all())

	def isDeveloper(self):
		empl = self.getEmployee()
		if not empl:
			return False
		return len(dbi.query(ProjectEmployee).filter(ProjectEmployee.employeeId == 
			empl.id).filter(ProjectEmployee.role == ROLE_DEVELOPER).all())

	def isManagerOnProject(self, projectId):
		empl = self.getEmployee()
		if not empl:
			return False
		return len(dbi.query(ProjectEmployee).filter(ProjectEmployee.employeeId == 
			empl.id).filter(ProjectEmployee.employeeId == projectId).filter(ProjectEmployee.role == 
				ROLE_MANAGER).all())

	def isTaskDeveloper(self, taskId):
		empl = self.getEmployee()
		if not empl:
			return False
		return len(dbi.query(Task).filter(Task.employeeId == 
			empl.id).filter(Task.id == taskId).all())

def getAppInstance():
	if App.instance is None:
		App.instance = App()
	return App.instance

appInst = getAppInstance()
