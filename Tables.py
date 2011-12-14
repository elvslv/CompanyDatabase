import sqlalchemy
import datetime
from design_files.widget_table import Ui_ViewTables
from main import appInst
from sqlalchemy import *
from Utils import *
from misc import *
from PyQt4 import QtGui, QtCore, Qt
from DB.Db import *

def getEdit(parent, field, val):
	if field.foreign_keys:
		return createComboBox(parent, field, val)
	if isinstance(field.type, Boolean):
		return createCheckBox(parent, field, val)
	if isinstance(field.type, DateTime):
		return createDateTimeEdit(parent, field, val)
	if isinstance(field.type, String) or isinstance(field.type, Text):
		return createLineEdit(parent, field, val)
	if (field.name in ('activity', 'stage', 'role')):
		return createComboBox(parent, field, val)
	if isinstance(field.type, Integer):
		return createIntegerBox(parent, field, val)

	showMessage('Error', 'Unknown type') ##just for debugging

def createIntegerBox(parent, field, val):
	result = QtGui.QSpinBox(parent)
	result.setMinimum(0)
	if val is not None:
		result.setValue(val)
	return result

def createLineEdit(parent, field, val):
	result = QtGui.QLineEdit(parent)
	if val is not None:
		result.setText(val)
	return result

def createDateTimeEdit(parent, field, val):
	dt = QtCore.QDateTime.currentDateTime() if val is None else QtCore.QDateTime.fromString(datetime.datetime.__str__(val), QtCore.Qt.ISODate)
	result = QtGui.QDateTimeEdit(dt, parent)
	return result

def createComboBox(parent, field, val):
	result = QtGui.QComboBox(parent)
	if isEnum(field):
		items = globals()[field.name]
	else:
		items = appInst.getForeignValues(parent.table, field)
	for i, item in enumerate(items):
		if parent.table.name == 'contracts' and field.name == 'companyId' and i == 0:
			continue
		if field.name in ('activity', 'stage', 'role'):
			result.addItem(item, i)
		else:
			result.addItem(item[1], item[0])
		
		if not(val == None) and (item[0] == val):
			result.setCurrentIndex(i)
	return result
	
def checkCorrectProjectAndContract(projectId, employeeId):
	project = dbi.query(Project).filter(Project.id == projectId).one()
	if project.finished:
		raise DBException('Project is finished')
		
	empl = dbi.query(Employee).filter(Employee.id == employeeId).one()
	contract = dbi.query(Contract).filter(Contract.projectId == projectId).filter(
		Contract.companyId == empl.companyId).all()
	if not len(contract) and empl.companyId != 1:
		raise DBException('Invalid pair: employee and project')
	if len(contract) and contract[0].activity != ACTIVITY_CONTRACT_MADE:
		raise DBException('Contract is terminated')

def createCheckBox(parent, field, val):
	result = QtGui.QCheckBox(parent)
	if val is not None:
		result.setChecked(val == 1)
	return result

class ChangeRecord(QtGui.QDialog):
	addUserSignal = QtCore.pyqtSignal(str)
	def __init__(self, parent, tableName, keys = None):
		super(ChangeRecord, self).__init__(parent)

		self.tableView = parent
		self.setModal(True)
		self.gbox = QtGui.QGridLayout(self)
		self.buttonBox = QtGui.QDialogButtonBox(self)
		self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
		self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
		self.buttonBox.setCenterButtons(True)
		
		self.table = appInst.getTable(tableName)
		self.fields = appInst.getVisibleHeaders(self.table)
		
		self.rec = None
		self.keys = keys
		if keys:
			self.rec = appInst.getRecord(tableName, keys)
		self.createEdits()
		self.buttonBox.accepted.connect(self.checkCorrectness)
		self.buttonBox.rejected.connect(self.reject)

	def createEdits(self):
		row = 0
		self.edits = []
		for i, field in enumerate(self.fields):
			if self.table.name == 'tasks' and field.name == 'state':
				continue
			label = QtGui.QLabel(self)
			label.setText(self.headers[i])
			self.gbox.addWidget(label, row, 0, 1, 1)
			edit = getEdit(self, field, self.rec[i] if self.rec else None)
			edit.field = field.name
			self.edits.append(edit)
			self.gbox.addWidget(edit, row, 1, 1, 1)
			row += 1

		self.gbox.addWidget(self.buttonBox, row + (1 if self.table.name == 'tasks' else 0), 1, 1, 1)
		self.setLayout(self.gbox)
		
	def checkCorrectness(self):
		if not self.editsAreNotEmpty():
			showMessage('Error', 'Fields must not be empty')
			return
		if self.rec:
			self.editRecord()
		else:
			self.addRecord()

	def getValue(self, edit):
		if isinstance(edit, QtGui.QSpinBox):
			return edit.value()
		if isinstance(edit, QtGui.QLineEdit):
			return edit.text()
		if isinstance(edit, QtGui.QComboBox):
			val = QtCore.QVariant.toString(edit.itemData(edit.currentIndex()))
			if val is None:
				val = edit.currentText()
			return val
		if isinstance(edit, QtGui.QCheckBox):
			return edit.isChecked()
		if isinstance(edit, QtGui.QDateTimeEdit):
			return edit.dateTime().toString(QtCore.Qt.ISODate)
		showMessage('Error', 'Unknown edit type')

	def getValues(self):
		self.values = list()
		for i, edit in enumerate(self.edits):
			self.values.append({'name': edit.field, 'value': self.getValue(edit)})
	
	def addRecord(self):
		self.getValues()
		appInst.insert(self.table, self.values)
		appInst.updateTableViews()
		self.close()

	def editRecord(self):
		values = dict()
		for i, edit in enumerate(self.edits):
			values[edit.field] = self.getValue(edit)
		appInst.update(self.table, self.keys, values)
		appInst.updateTableViews()
		self.close()

	def editsAreNotEmpty(self):
		correct = True
		for edit in self.edits:
			if isinstance(edit, QtGui.QSpinBox):
				correct = correct and edit.value()
			if isinstance(edit, QtGui.QLineEdit):
				correct = correct and len(edit.text())
			if isinstance(edit, QtGui.QComboBox):
				correct = correct and len(edit.currentText())
			if isinstance(edit, QtGui.QDateTimeEdit):
				correct = correct and len(edit.dateTime().toString(QtCore.Qt.ISODate))
		return correct

class ChangeRecordCompany(ChangeRecord):
	def __init__(self, parent, tableName, keys = None):
		self.headers = ['name', 'details']
		super(ChangeRecordCompany, self).__init__(parent, tableName, keys)
		
	def checkCorrectness(self):
		if not self.editsAreNotEmpty():
			showMessage('Error', 'Fields must not be empty')
			return
		correct = True
		for edit in self.edits:
			correct = correct and len(edit.text()) > 0
		if not correct:
			showMessage('Error', 'Company name and details must not be empty')
			return False
		if self.rec:
			self.editRecord()
		else:
			self.addRecord()

class ChangeRecordUsers(ChangeRecord):
	def __init__(self, parent, tableName, keys = None):
		self.headers = ['login', 'password', 'has admin permissions']
		super(ChangeRecordUsers, self).__init__(parent, tableName, keys)

	def addRecord(self):
		super(ChangeRecordUsers, self).addRecord()
		self.tableView.addUserSignal.emit(self.values[0]['value'])
	
	def checkCorrectness(self):
		if not self.editsAreNotEmpty():
			showMessage('Error', 'Fields must not be empty')
			return

		correct = True
		for edit in self.edits:
			if edit.field == 'login':
				correct = correct and len(edit.text()) >= MIN_LOGIN_LENGTH
			elif edit.field == 'password':
				correct = correct and len(edit.text()) >= MIN_PASSWORD_LENGTH
		if not correct:
			showMessage('Error', 'Min login length is %d, min password length is%d'%(
				MIN_LOGIN_LENGTH, MIN_PASSWORD_LENGTH))
			return False
		if self.rec:
			self.editRecord()
		else:
			self.addRecord()

class ChangeRecordEmployees(ChangeRecord):
	def __init__(self, parent, tableName, keys = None):
		self.headers = ['name', 'company', 'login']
		super(ChangeRecordEmployees, self).__init__(parent, tableName, keys)
		self.addUserSignal.connect(self.addedUser)
		
	def checkCorrectness(self):
		if not self.editsAreNotEmpty():
			showMessage('Error', 'Fields must not be empty')
			return

		if self.rec:
			self.editRecord()
		else:
			self.addRecord()

	def createEdits(self):
		self.edits = []
		label = QtGui.QLabel(self)
		label.setText('name')
		self.gbox.addWidget(label, 0, 0)
		edit = createLineEdit(self, self.fields[0], self.rec[0] if self.rec else None)
		edit.field = 'name'
		self.edits.append(edit)
		self.gbox.addWidget(edit, 0, 1)

		label = QtGui.QLabel(self)
		label.setText('company')
		self.gbox.addWidget(label, 1, 0)
		edit = createComboBox(self, self.fields[1], self.rec[1] if self.rec else None)
		edit.field = self.fields[1].name
		self.edits.append(edit)
		self.gbox.addWidget(edit, 1, 1)

		label = QtGui.QLabel(self)
		label.setText('login')
		self.gbox.addWidget(label, 2, 0)
		edit = createLineEdit(self, None, self.rec[2] if self.rec else None)
		edit.field = 'login'
		edit.setDisabled(True)
		self.edits.append(edit)
		self.gbox.addWidget(edit, 2, 1)
		if not self.rec:
			addUserBtn = QtGui.QPushButton(self)
			addUserBtn.setText('Add user')
			self.gbox.addWidget(addUserBtn, 2, 2)
			addUserBtn.clicked.connect(self.addUser)

		self.gbox.addWidget(self.buttonBox, 4, 1)
		self.setLayout(self.gbox)

	def addUser(self):
		newUser = ChangeRecordUsers(self, 'users')
		newUser.open()

	@QtCore.pyqtSlot(str)
	def addedUser(self, login):
		self.edits[-1].setText(login)

class ChangeRecordProjects(ChangeRecord):
	def __init__(self, parent, tableName, keys = None):
		self.headers = ['name', 'start date', 'is finished']
		super(ChangeRecordProjects, self).__init__(parent, tableName, keys)
		
	def checkCorrectness(self):
		if not self.editsAreNotEmpty():
			showMessage('Error', 'Fields must not be empty')
			return
		self.getValues()
		if self.rec:
			startDate = self.values[1]['value']
			if len(dbi.session.execute('''select 1 from jobs as a, tasks as b, projects as c where
				a.taskId = b.id and c.name = "%s" and b.projectId = c.id and unix_timestamp(a.startDate) < %s''' % (self.rec[0], 
					QtCore.QDateTime.fromString(startDate).toTime_t())).fetchall()):
				showMessage('Error', 'Task jobs can not start earlier than project')
				return
			self.editRecord()
		else:
			self.addRecord()

class ChangeRecordContracts(ChangeRecord):
	def __init__(self, parent, tableName, keys = None):
		self.headers = ['company', 'project', 'contract state']
		super(ChangeRecordContracts, self).__init__(parent, tableName, keys)

	def checkCorrectness(self):
		if not self.editsAreNotEmpty():
			showMessage('Error', 'Fields must not be empty')
			return
		self.getValues()
		project = dbi.query(Project).filter(Project.id == self.values[1]['value']).one()
		if project.finished:
			showMessage('Error', 'Can not make contract on finished project')
			return
		if self.rec:
			self.editRecord()
		else:
			self.addRecord()


class ChangeRecordProjectEmployees(ChangeRecord):
	def __init__(self, parent, tableName, keys = None):
		self.headers = ['employee', 'project', 'role']
		super(ChangeRecordProjectEmployees, self).__init__(parent, tableName, keys)
		
	def checkCorrectness(self):
		if not self.editsAreNotEmpty():
			showMessage('Error', 'Fields must not be empty')
			return
		self.getValues()
		try:
			checkCorrectProjectAndContract(self.values[1]['value'], self.values[0]['value'])
		except DBException, e:
			showMessage('Error', e.value)
			return
		if self.rec:
			self.editRecord()
		else:
			self.addRecord()

class ChangeRecordTasks(ChangeRecord):
	def __init__(self, parent, tableName, keys = None):
		self.headers = ['name', 'project', 'employee', 'planned time']
		super(ChangeRecordTasks, self).__init__(parent, tableName, keys)

	def createEdits(self):
		super(ChangeRecordTasks, self).createEdits()
		label = QtGui.QLabel(self)
		label.setText('Finished')
		self.gbox.addWidget(label, 4, 0)
		self.checkBox = QtGui.QCheckBox(self)
		self.gbox.addWidget(self.checkBox, 4, 1)

	def getValues(self):
		super(ChangeRecordTasks, self).getValues()
		if self.checkBox.isChecked():
			self.values.append({'name': 'state', 'value': STAGE_TASK_FINISHED})
		elif self.rec:
			if len(dbi.session.execute('select 1 from jobs where taskId=%s' % self.keys[0]['value']).fetchall()):
				self.values.append({'name': 'state', 'value': STAGE_TASK_IN_PROGRESS})
			else:
				self.values.append({'name': 'state', 'value': STAGE_TASK_NOT_STARTED})

	def checkCorrectness(self):
		if not self.editsAreNotEmpty():
			showMessage('Error', 'Fields must not be empty')
			return
		self.getValues()
		
		projectId = self.values[1]['value']
		employeeId = self.values[2]['value']
		try:
			checkCorrectProjectAndContract(projectId, employeeId)
		except DBException, e:
			showMessage('Error', e.value)
			return
		if (self.rec and len(dbi.query(Task).filter(Task.employeeId == employeeId).filter(
			Task.state != STAGE_TASK_FINISHED).filter(Task.id != self.keys[0]['value']).all())) or\
			(not self.rec and len(dbi.query(Task).filter(Task.employeeId == employeeId).filter(
			Task.state != STAGE_TASK_FINISHED).all())):
			showMessage('Error', 'Employee has tasks in progress')
			return
		if self.rec:
			if self.checkBox.isChecked():
				if len(dbi.query(TasksDependency, Task).filter(TasksDependency.slaveId == 
					self.keys[0]['value']).filter(Task.id == TasksDependency.masterId).filter(
						Task.state != STAGE_TASK_FINISHED).all()):
					showMessage('Error', 'There are unfinished task dependencies')
					return
			else:
				if len(dbi.session.execute('''select 1 from tasksDependencies as a, 
					tasks as b where a.masterId=%s and b.id=a.slaveId and b.state=%s''' %(
					self.keys[0]['value'], STAGE_TASK_FINISHED)).fetchall()):
					showMessage('Error', 'There are finished dependent tasks')
					return
		if self.rec:
			self.editRecord()
		else:
			self.addRecord()

	def editRecord(self):
		values = dict()
		for i, edit in enumerate(self.edits):
			values[edit.field] = self.getValue(edit)
		if self.values[len(self.values) - 1]['name'] == 'state':
			values['state'] = self.values[len(self.values) - 1]['value']
		appInst.update(self.table, self.keys, values)
		appInst.updateTableViews()
		self.close()

class ChangeRecordJobs(ChangeRecord):
	def __init__(self, parent, tableName, keys = None):
		self.headers = ['employee', 'task', 'start date', 'completion date', 'description']
		super(ChangeRecordJobs, self).__init__(parent, tableName, keys)
	
	def checkCorrectness(self):
		if not self.editsAreNotEmpty():
			showMessage('Error', 'Fields must not be empty')
			return
		self.getValues()
		task = dbi.query(Task).filter(Task.id == self.values[1]['value']).one()
		if task.state == STAGE_TASK_FINISHED:
			showMessage('Error', 'Task is finished')
			return
		try:
			checkCorrectProjectAndContract(task.projectId, self.values[0]['value'])
		except DBException, e:
			showMessage('Error', e.value)
			return
		startDate = self.values[2]['value']
		completionDate = self.values[3]['value']
		if startDate >= completionDate:
			showMessage('Error', 'Start date must be earlier than completion date')
			return
		projDate = dbi.session.execute('''select a.startDate from projects as a, tasks as b 
			where a.id = b.projectId and b.id = %s''' % self.values[1]['value']).fetchone()
		if datetime.datetime.strptime(str(startDate), "%Y-%m-%dT%H:%M:%S") < projDate[0]:
			showMessage('Error', 'Task jobs can not start earlier than project')
			return
		if self.rec:
			self.editRecord()
		else:
			self.addRecord()


class ChangeRecordTaskDependencies(ChangeRecord):
	def __init__(self, parent, tableName, keys = None):
		self.headers = ['master', 'slave']
		super(ChangeRecordTaskDependencies, self).__init__(parent, tableName, keys)

	def checkCorrectness(self):
		if not self.editsAreNotEmpty():
			showMessage('Error', 'Fields must not be empty')
			return
		self.getValues()
		masterId = int(self.values[0]['value'])
		slaveId = int(self.values[1]['value'])
		project1 = appInst.getProjectByTask(masterId)
		project2 = appInst.getProjectByTask(slaveId)
		if project1.id != project2.id:
			showMessage('Error', 'Chosen tasks must belong to the same project')
			return
		if masterId == slaveId:
			showMessage('Error', 'Chosen tasks must be different')
			return
		graph, maxTaskId = appInst.getTasksDependencyGraph(slaveId)
		if graph:
			graph[slaveId].append(masterId)
			vis = [False for i in range(maxTaskId + 1)]
			
			def dfs(v):
				if vis[v]:
					return True
				vis[v] = True
				for i in graph[v]:
					if dfs(i):
						return True
				vis[v] = False
				return False
				
			if dfs(slaveId):
				showMessage('Error', 'Cycle detected')
				return
			
		if self.rec:
			self.editRecord()
		else:
			self.addRecord()

class ViewTables(QtGui.QWidget):
	def __init__(self, parent, tableName, isReport = None):
		super(ViewTables, self).__init__(parent)

		self.ui = Ui_ViewTables()
		self.ui.setupUi(self)

		self.ui.addRecordButton.clicked.connect(self.addRecord)
		self.ui.editRecordButton.clicked.connect(self.editRecord)
		self.ui.deleteRecordButton.clicked.connect(self.deleteRecord)
		self.ui.tableWidget.itemSelectionChanged.connect(self.disableButtons)
		self.tableName = tableName
		self.setWindowTitle(convertTableNameToTitle[tableName])
		self.isReport = isReport
		appInst.tables.append(self)
		self.fillHeaders()
		self.fillCells()
		self.disableButtons()

	def fillHeaders(self):
		#self.headers = appInst.getHeadersWithForeignValues(self.tableName)
		self.ui.tableWidget.setColumnCount(len(self.headers))
		self.ui.tableWidget.verticalHeader().setVisible(False)
		self.ui.tableWidget.setHorizontalHeaderLabels(self.headers)
		if not appInst.isAdmin():
			self.ui.addRecordButton.setDisabled(True)

	def fillCells(self):
		self.ui.tableWidget.clearContents()
		fields = appInst.getVisibleHeaders(appInst.getTable(self.tableName))
		values = appInst.selectAllWithForeignValues(self.tableName, self.isReport)
		self.ui.tableWidget.setRowCount(len(values) + (1 if self.isReport else 0))
		row = -1
		for value in values:
			row = row + 1
			column = -1
			for item in value:
				column = column + 1
				it = item
				if isEnum(fields[column]):
					it = globals()[fields[column].name][int(item)]
				newitem = QtGui.QTableWidgetItem(str(it))
				self.ui.tableWidget.setItem(row, column, newitem)
		
		if self.isReport:
			newitem = QtGui.QTableWidgetItem(str(appInst.cntSum()))
			self.ui.tableWidget.setItem(row + 1, column, newitem)
			
			
		self.primaryKeys = self.findPrimaryKeys()
		
	def findPrimaryKeys(self):
		fields = appInst.getHeaders(self.tableName)
		values = appInst.selectAll(self.tableName)
		result = list()
		
		for value in values:
			pk = list()
			column = -1
			for item in value:
				column += 1
				if fields[column].primary_key:
					pk.append({'name': fields[column].name, 'value': item})
			result.append(pk)
			
		return result

	def disableButtons(self):
		disable = not (appInst.isAdmin() and len(self.ui.tableWidget.selectedItems()))
		self.ui.addRecordButton.setDisabled(not appInst.isAdmin())
		self.ui.editRecordButton.setDisabled(disable)
		self.ui.deleteRecordButton.setDisabled(disable)
	
	def addRecord(self):
		rec = ChangeRecord(self, self.tableName)
		rec.open()

	def editRecord(self):
		row = self.ui.tableWidget.currentRow()
		rec = ChangeRecord(self, self.tableName, self.primaryKeys[row])
		rec.open()

	def deleteRecord(self):
		msg = QtGui.QMessageBox.question(self, 'Message',
			'Are you sure to delete this record ?',
			QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
		if msg == QtGui.QMessageBox.Yes:
			row = self.ui.tableWidget.currentRow()
			appInst.delete(self.tableName, self.primaryKeys[row])
			appInst.updateTableViews()

	def closeEvent(self, event):
		appInst.tables.remove(self)
		event.accept()

class ViewTableCompanies(ViewTables):
	def __init__(self, parent):
		self.headers = ['name', 'details']
		super(ViewTableCompanies, self).__init__(parent, 'companies')

	def addRecord(self):
		rec = ChangeRecordCompany(self, self.tableName)
		rec.open()

	def editRecord(self):
		row = self.ui.tableWidget.currentRow()
		rec = ChangeRecordCompany(self, self.tableName, self.primaryKeys[row])
		rec.open()

	def disableButtons(self):
		super(ViewTableCompanies, self).disableButtons()
		row = self.ui.tableWidget.currentRow()
		disable = not appInst.isAdmin() or (appInst.isAdmin() and self.primaryKeys[row][0]['value'] == 1)
		self.ui.deleteRecordButton.setDisabled(disable)

class ViewTableUsers(ViewTables):
	def __init__(self, parent):
		self.headers = ['login', 'admin']
		super(ViewTableUsers, self).__init__(parent, 'users')

	def addRecord(self):
		rec = ChangeRecordUsers(self, self.tableName)
		rec.open()

	def editRecord(self):
		row = self.ui.tableWidget.currentRow()
		rec = ChangeRecordUsers(self, self.tableName, self.primaryKeys[row])
		rec.open()

	def disableButtons(self):
		self.ui.addRecordButton.setDisabled(not appInst.isAdmin())
		disable = not (appInst.isAdmin() and len(self.ui.tableWidget.selectedItems()))
		if len(self.ui.tableWidget.selectedItems()):
			row = self.ui.tableWidget.currentRow()
			user = appInst.getRecord('users', self.primaryKeys[row])
			disable = user.login != appInst.getLogin() and not appInst.isAdmin()
		
		self.ui.editRecordButton.setDisabled(disable)
		disable = disable or len(appInst.getAdmins()) == 1
		self.ui.deleteRecordButton.setDisabled(disable)

class ViewTableEmployees(ViewTables):
	def __init__(self, parent):
		self.headers = ['name', 'company', 'login']
		super(ViewTableEmployees, self).__init__(parent, 'employees')

	def addRecord(self):
		rec = ChangeRecordEmployees(self, self.tableName)
		rec.open()

	def editRecord(self):
		row = self.ui.tableWidget.currentRow()
		rec = ChangeRecordEmployees(self, self.tableName, self.primaryKeys[row])
		rec.open()

class ViewTableProjects(ViewTables):
	def __init__(self, parent):
		self.headers = ['name', 'start date', 'is finished']
		super(ViewTableProjects, self).__init__(parent, 'projects')

	def addRecord(self):
		rec = ChangeRecordProjects(self, self.tableName)
		rec.open()

	def editRecord(self):
		row = self.ui.tableWidget.currentRow()
		rec = ChangeRecordProjects(self, self.tableName, self.primaryKeys[row])
		rec.open()

class ViewTableContracts(ViewTables):
	def __init__(self, parent):
		self.headers = ['company', 'project', 'contract state']
		super(ViewTableContracts, self).__init__(parent, 'contracts')

	def addRecord(self):
		rec = ChangeRecordContracts(self, self.tableName)
		rec.open()

	def editRecord(self):
		row = self.ui.tableWidget.currentRow()
		rec = ChangeRecordContracts(self, self.tableName, self.primaryKeys[row])
		rec.open()

	def disableButtons(self):
		super(ViewTableContracts, self).disableButtons()
		#disable = not (appInst.isAdmin() and len(self.ui.tableWidget.selectedItems()))
		#disable = disable or not(appInst.hasProjects() and appInst.hasPartners())
		#self.ui.deleteRecordButton.setDisabled(disable)

class ViewTableProjectEmployees(ViewTables):
	def __init__(self, parent):
		self.headers = ['employee', 'project', 'role']
		super(ViewTableProjectEmployees, self).__init__(parent, 'projectEmployees')

	def addRecord(self):
		rec = ChangeRecordProjectEmployees(self, self.tableName)
		rec.open()

	def editRecord(self):
		row = self.ui.tableWidget.currentRow()
		rec = ChangeRecordProjectEmployees(self, self.tableName, self.primaryKeys[row])
		rec.open()

	def disableButtons(self):
		canAdd = appInst.isAdmin() or appInst.isManager()
		self.ui.addRecordButton.setDisabled(not canAdd)
		canChange = appInst.isAdmin() and len(self.ui.tableWidget.selectedItems())
		if len(self.ui.tableWidget.selectedItems()):
			row = self.ui.tableWidget.currentRow()
			projectEmpolyee = appInst.getRecord('projectEmployees', self.primaryKeys[row])
			canChange = canChange or appInst.isManagerOnProject(projectEmpolyee.projectId)
		self.ui.editRecordButton.setDisabled(not canChange)
		self.ui.deleteRecordButton.setDisabled(not canChange)

class ViewTableTasks(ViewTables):
	def __init__(self, parent):
		self.headers = ['name', 'project', 'employee', 'planned time', 'state']
		super(ViewTableTasks, self).__init__(parent, 'tasks')

	def addRecord(self):
		rec = ChangeRecordTasks(self, self.tableName)
		rec.open()

	def editRecord(self):
		row = self.ui.tableWidget.currentRow()
		rec = ChangeRecordTasks(self, self.tableName, self.primaryKeys[row])
		rec.open()

	def disableButtons(self):
		canAdd = appInst.isAdmin() or appInst.isManager()
		self.ui.addRecordButton.setDisabled(not canAdd)
		canChange = appInst.isAdmin() and len(self.ui.tableWidget.selectedItems())
		if len(self.ui.tableWidget.selectedItems()):
			row = self.ui.tableWidget.currentRow()
			task = appInst.getRecord('tasks', self.primaryKeys[row])
			canChange = canChange or appInst.isManagerOnProject(task.projectId) or\
				appInst.isTaskDeveloper(task.id)
		self.ui.editRecordButton.setDisabled(not canChange)
		self.ui.deleteRecordButton.setDisabled(not canChange)


class ViewTableJobs(ViewTables):
	def __init__(self, parent, isReport):
		self.projects = None
		self.headers = ['employee', 'task', 'description', 'time spent'] if isReport else ['employee', 'task', 'start date', 'completion date', 'description'] 
		super(ViewTableJobs, self).__init__(parent, 'jobs', isReport)
		
		if isReport:
			self.ui.addRecordButton.setVisible(False)
			self.ui.editRecordButton.setVisible(False)
			self.ui.deleteRecordButton.setVisible(False)
			self.hLayout = QtGui.QHBoxLayout(self)
			align = QtCore.Qt.Alignment(0x0040)
			self.hLayout.setAlignment(align)
			self.setLayout(self.hLayout)
			self.createFilters()
			self.filterBtn = QtGui.QPushButton()
			self.filterBtn.setText('Filter')
			self.filterBtn.clicked.connect(self.filter)
			self.hLayout.addWidget(self.filterBtn)

	def filter(self):
		self.fillCells()

	def createFilters(self):
		self.projects = QtGui.QComboBox(self)
		items = [(None, 'Choose project')]
		items.extend(dbi.query(Project.id, Project.name).all())
		for i, item in enumerate(items):
			self.projects.addItem(item[1], item[0])
		self.hLayout.addWidget(self.projects)
		
		self.employees = QtGui.QComboBox(self)
		items = [(None, 'Choose employee')]
		items.extend(dbi.query(Employee.id, Employee.name).all())
		for i, item in enumerate(items):
			self.employees.addItem(item[1], item[0])
		self.hLayout.addWidget(self.employees)
		
		self.tasks = QtGui.QComboBox(self)
		items = [(None, 'Choose task')]
		items.extend(dbi.query(Task.id, Task.name).all())
		for i, item in enumerate(items):
			self.tasks.addItem(item[1], item[0])
		self.hLayout.addWidget(self.tasks)

	def getFilterParams(self):
		if not self.projects:
			return None
		result = dict()
		combos = [
			{'edit': self.projects, 'name': 'projectId'},
			{'edit': self.employees, 'name': 'employeeId'},
			{'edit': self.tasks, 'name': 'taskId'}
			]
		for c in combos:
			if not c['edit'].itemData(c['edit'].currentIndex()).isNull():
				result[c['name']] = QtCore.QVariant.toString(c['edit'].itemData(c['edit'].currentIndex()))
				
		return result
	
	def fillHeaders(self):
		super(ViewTableJobs, self).fillHeaders()
		if self.isReport:
			self.ui.tableWidget.setColumnCount(len(self.headers))
			self.ui.tableWidget.verticalHeader().setVisible(False)
			self.ui.tableWidget.setHorizontalHeaderLabels(self.headers)

	def fillCells(self):
		self.ui.tableWidget.clearContents()
		filterParams = self.getFilterParams()
		values = appInst.selectAllWithForeignValues(self.tableName, self.isReport, filterParams)
		self.ui.tableWidget.setRowCount(len(values) + (1 if self.isReport else 0))
		row = -1
		column = 0
		for value in values:
			row = row + 1
			column = -1
			for item in value:
				column = column + 1
				it = datetime.timedelta(seconds = item) if column == 3 and self.isReport else item
				newitem = QtGui.QTableWidgetItem(str(it))
				self.ui.tableWidget.setItem(row, column, newitem)
		
		if self.isReport:
			sum = appInst.cntSum(filterParams)
			if sum:
				newitem = QtGui.QTableWidgetItem(str(sum))
				self.ui.tableWidget.setItem(row + 1, column, newitem)

		self.primaryKeys = self.findPrimaryKeys()

	def addRecord(self):
		rec = ChangeRecordJobs(self, self.tableName)
		rec.open()

	def editRecord(self):
		row = self.ui.tableWidget.currentRow()
		rec = ChangeRecordJobs(self, self.tableName, self.primaryKeys[row])
		rec.open()

	def disableButtons(self):
		canAdd = appInst.isAdmin() or appInst.isManager() or\
			appInst.isDeveloper()
		self.ui.addRecordButton.setDisabled(not canAdd)
		canChange = appInst.isAdmin() and len(self.ui.tableWidget.selectedItems())
		if len(self.ui.tableWidget.selectedItems()):
			row = self.ui.tableWidget.currentRow()
			job = appInst.getRecord('jobs', self.primaryKeys[row])
			task = dbi.query(Task).filter(Task.id == job.taskId).one()
			canChange = canChange or appInst.isManagerOnProject(task.projectId) or\
				appInst.isTaskDeveloper(task.id)
		self.ui.editRecordButton.setDisabled(not canChange)
		self.ui.deleteRecordButton.setDisabled(not canChange)

class ViewTableTaskDependencies(ViewTables):
	def __init__(self, parent):
		self.headers = ['master', 'slave']
		super(ViewTableTaskDependencies, self).__init__(parent, 'tasksDependencies')

	def addRecord(self):
		rec = ChangeRecordTaskDependencies(self, self.tableName)
		rec.open()

	def editRecord(self):
		row = self.ui.tableWidget.currentRow()
		rec = ChangeRecordTaskDependencies(self, self.tableName, self.primaryKeys[row])
		rec.open()

	def disableButtons(self):
		canAdd = appInst.isAdmin() and appInst.getMaxTasksNumOnProjects()> 1 or\
			appInst.isManager() and appInst.getMaxTasksNumOnProjectsWithManager() > 1
		self.ui.addRecordButton.setDisabled(not canAdd)
		canChange = appInst.isAdmin() and len(self.ui.tableWidget.selectedItems())
		if len(self.ui.tableWidget.selectedItems()):
			row = self.ui.tableWidget.currentRow()
			taskDependency = appInst.getRecord('tasksDependencies', self.primaryKeys[row])
			project1 = appInst.getProjectByTask(taskDependency.masterId)
			project2 = appInst.getProjectByTask(taskDependency.slaveId)
			canChange = canChange or (appInst.isManagerOnProject(project1.id) and\
				project1.id == project2.id)
		self.ui.editRecordButton.setDisabled(not canChange)
		self.ui.deleteRecordButton.setDisabled(not canChange)
		
