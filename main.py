from PyQt4 import QtGui, QtCore
from DB.Db import *
from sqlalchemy.orm.exc import NoResultFound
from DB.dbExceptions import DBException
from sqlalchemy import *
from sqlalchemy.sql import *
from Utils import *
import math
import datetime

class AppUser:
	def __init__(self, login = None, password = None, admin = False):
		self.login = login
		self.password = password
		self.admin = admin

class App:
	instance = None
	curUser = None 
	
	def __init__(self):
		self.tables = list()

	def getUser(self, login, password):
		return dbi.query(User).filter(login == User.login).filter(password == User.password).one()

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
		return not(column.primary_key and\
			isinstance(column.type, Integer) and not column.foreign_keys)

	def getHeadersWithForeignValues(self, tableName):
		table = self.getTable(tableName)
		columns = []
		for column in table.columns:
			if self.isVisible(column) and column.name != 'password':
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

	def selectAllWithForeignValues(self, tableName, isReport = None, filterParams = None):
		table = self.getTable(tableName)
		columns = []
		filterStmts = dict()
		for column in table.columns:
			if not(self.isVisible(column)) or column.name == 'password':
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
			qStr = '''select c.name, b.name, a.description, unix_timestamp(a.completionDate) 
				- unix_timestamp(a.startDate) from jobs as a, tasks as b, employees as c 
				where a.employeeId = c.id and b.id = a.taskId'''
			if filterParams:
				if 'employeeId' in filterParams:
					qStr += ' and c.id = %s' % filterParams['employeeId']
				if 'taskId' in filterParams:
					qStr += ' and b.id = %s' % filterParams['taskId']
				if 'projectId' in filterParams:
					qStr += ' and b.projectId = %s' % filterParams['projectId']
					
			q = dbi.session.execute(qStr).fetchall()
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
		if str(table) == 'jobs':
			taskId = tmp.taskId
		dbi.addUnique(tmp)
		if str(table) == 'jobs':
			task = dbi.query(Task).filter(Task.id == taskId).one()
			if len(task.jobs) and task.state == STAGE_TASK_NOT_STARTED:
				task.state = STAGE_TASK_IN_PROGRESS
				dbi.flush(task)

	def update(self, table, keys, values):
		table = tableClasses[table.name]
		obj = dbi.query(table)
		for key in keys:
			obj = obj.filter(getattr(table, key['name']) == key['value'])
		if table is Job:
			oldTaskId = obj.one().taskId
		obj.update(values)
		if table is Job:
			task = dbi.query(Task).filter(Task.id == oldTaskId).one()
			if not len(task.jobs):
				task.state = STAGE_TASK_NOT_STARTED
				dbi.flush(task)
			newTask = obj.one().task
			if len(newTask.jobs) and newTask.state == STAGE_TASK_NOT_STARTED:
				newTask.state = STAGE_TASK_IN_PROGRESS
				dbi.flush(newTask)

	def delete(self, table, keys):
		table = tableClasses[table]
		obj = dbi.query(table)
		for key in keys:
			obj = obj.filter(getattr(table, key['name']) == key['value'])
		if table is Job:
			task = obj.one().task
		obj.delete()
		if table is Job:
			if not len(task.jobs):
				task.state = STAGE_TASK_NOT_STARTED
				dbi.flush(task)

	def updateTableViews(self):
		for table in self.tables:
			table.fillCells()
			
	def disableButtons(self):
		for table in self.tables:
			table.disableButtons()

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
		projects = dbi.query(ProjectEmployee).filter(ProjectEmployee.employeeId == 
			self.getEmployee().id).filter(ProjectEmployee.role == ROLE_MANAGER).all()
		maxi = 0
		for project in projects:
			m = self.getTasksNumOnProject(project.projectId)
			if m > maxi:
				maxi = m
		return maxi

	def getProjectByTask(self, taskId):
		return dbi.query(Task).filter(taskId == Task.id).one().project

	def getTasksDependencyGraph(self, slaveId):
		query = dbi.query(TasksDependency.slaveId, 
			TasksDependency.masterId).group_by(TasksDependency.slaveId).all()
		maxId = dbi.query(func.max(TasksDependency.slaveId)).scalar()
		if not maxId:
			return None, None
		maxTaskId = dbi.query(func.max(Task.id)).scalar()
		graph = [[] for i in range(max(maxId, slaveId) + 1)]
		for q in query:
			graph[q[0]].append(q[1])
		return graph, maxTaskId

	def isAdmin(self):
		return self.curUser and self.curUser.admin

	def getLogin(self):
		return self.curUser.login if self.curUser else None

	def getEmployee(self):
		return dbi.query(Employee).filter(self.curUser.login == Employee.login).one() if self.curUser else None
		
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
			empl.id).filter(ProjectEmployee.projectId == projectId).filter(ProjectEmployee.role == 
				ROLE_MANAGER).all())

	def isTaskDeveloper(self, taskId):
		empl = self.getEmployee()
		if not empl:
			return False
		return len(dbi.query(Task).filter(Task.employeeId == 
			empl.id).filter(Task.id == taskId).all())

	def cntSum(self, filterParams = None):
		qStr = '''select sum(unix_timestamp(completionDate) - unix_timestamp(startDate)) from jobs as a, 
			tasks as b, employees as c where a.employeeId = c.id and b.id = a.taskId'''
		if filterParams:
			if 'employeeId' in filterParams:
				qStr += ' and c.id = %s' % filterParams['employeeId']
			if 'taskId' in filterParams:
				qStr += ' and b.id = %s' % filterParams['taskId']
			if 'projectId' in filterParams:
				qStr += ' and b.projectId = %s' % filterParams['projectId']
		res = dbi.session.execute(qStr).fetchone()[0]
		return datetime.timedelta(seconds = int(res)) if res else 0

	def getNotEmptyProjects(self):
		return dbi.session.execute('''select * from projects where id in 
			(select projectId from tasks)''').fetchall()

def getAppInstance():
	if App.instance is None:
		App.instance = App()
	return App.instance

appInst = getAppInstance()
