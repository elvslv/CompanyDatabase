import sqlalchemy
from design_files.widget_table import Ui_ViewTables
from main import appInst
from sqlalchemy import *
from Utils import *
from misc import *
from PyQt4 import QtGui, QtCore
from DB.Db import *

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
		
		self.table = appInst.curUser.getTable(tableName)
		self.fields = appInst.curUser.getVisibleHeaders(self.table)
		
		self.rec = None
		self.keys = keys
		if keys:
			self.rec = appInst.curUser.getRecord(tableName, keys)
		self.createEdits()
		self.buttonBox.accepted.connect(self.checkCorrectness)
		self.buttonBox.rejected.connect(self.reject)

	def createEdits(self):
		row = 0
		self.edits = []
		for i, field in enumerate(self.fields):
			label = QtGui.QLabel(self)
			label.setText(appInst.getColumnName(field))
			self.gbox.addWidget(label, row, 0, 1, 1)
			edit = self.getEdit(field, self.rec[i] if self.rec else None)
			edit.field = field.name
			self.edits.append(edit)
			self.gbox.addWidget(edit, row, 1, 1, 1)
			row += 1
			
		self.gbox.addWidget(self.buttonBox, row, 1, 1, 1)
		self.setLayout(self.gbox)

	def getEdit(self, field, val):
		if field.foreign_keys:
			return self.createComboBox(field, val)
		if isinstance(field.type, Boolean):
			return self.createCheckBox(field, val)
		if isinstance(field.type, DateTime):
			return self.createDateTimeEdit(field, val)
		if isinstance(field.type, String) or isinstance(field.type, Text):
			return self.createLineEdit(field, val)
		if (field.name in ('activity', 'stage', 'role')):
			return self.createComboBox(field, val)
		if isinstance(field.type, Integer):
			return self.createIntegerBox(field, val)

		showMessage('Error', 'Unknown type') ##just for debugging

	def createIntegerBox(self, field, val):
		result = QtGui.QSpinBox(self)
		result.setMinimum(0)
		if val is not None:
			result.setValue(val)
		return result
	
	def createLineEdit(self, field, val):
		result = QtGui.QLineEdit(self)
		if val is not None:
			result.setText(val)
		return result

	def createDateTimeEdit(self, field, val):
		datetime = QtCore.QDateTime.currentDateTime() if val is None else QtCore.QDateTime.fromString(val, QtCore.Qt.ISODate)
		result = QtGui.QDateTimeEdit(datetime, self)
		return result

	def createComboBox(self, field, val):
		result = QtGui.QComboBox(self)
		if isEnum(field):
			items = globals()[field.name]
		else:
			items = appInst.curUser.getForeignValues(self.table, field)
		for i, item in enumerate(items):
			if field.name in ('activity', 'stage', 'role'):
				result.addItem(item, i)
			else:
				result.addItem(item[1], item[0])
			if not(val == None) and (item[0] == val):
				result.setCurrentIndex(i)
		return result

	def createCheckBox(self, field, val):
		result = QtGui.QCheckBox(self)
		if val is not None:
			result.setChecked(val == 1)
		return result
		
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
		appInst.curUser.insert(self.table, self.values)
		appInst.updateTableViews()
		self.close()

	def editRecord(self):
		values = dict()
		for i, edit in enumerate(self.edits):
			values[edit.field] = self.getValue(edit)
		appInst.curUser.update(self.table, self.keys, values)
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
		edit = self.createLineEdit(self.fields[0], self.rec[0] if self.rec else None)
		edit.field = 'name'
		self.edits.append(edit)
		self.gbox.addWidget(edit, 0, 1)

		label = QtGui.QLabel(self)
		label.setText('company')
		self.gbox.addWidget(label, 1, 0)
		edit = self.createComboBox(self.fields[1], self.rec[1] if self.rec else None)
		edit.field = self.fields[1].name
		self.edits.append(edit)
		self.gbox.addWidget(edit, 1, 1)

		label = QtGui.QLabel(self)
		label.setText('login')
		self.gbox.addWidget(label, 2, 0)
		edit = self.createLineEdit(None, self.rec[2] if self.rec else None)
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
		super(ChangeRecordProjects, self).__init__(parent, tableName, keys)
		
	def checkCorrectness(self):
		if not self.editsAreNotEmpty():
			showMessage('Error', 'Fields must not be empty')
			return
		if self.rec:
			self.editRecord()
		else:
			self.addRecord()

class ChangeRecordContracts(ChangeRecord):
	def __init__(self, parent, tableName, keys = None):
		super(ChangeRecordContracts, self).__init__(parent, tableName, keys)

class ChangeRecordProjectEmployees(ChangeRecord):
	def __init__(self, parent, tableName, keys = None):
		super(ChangeRecordProjectEmployees, self).__init__(parent, tableName, keys)
		
	def checkCorrectness(self):
		if not self.editsAreNotEmpty():
			showMessage('Error', 'Fields must not be empty')
			return
		self.getValues()
		e = self.values[0]['value']
		p = self.values[1]['value']
		empl = dbi.query(Employee).filter(Employee.id == e).one()
		comp = dbi.query(Contract.companyId).filter(Contract.projectId == p).all()
		exists = False
		for c in comp:
			if c[0] == empl.companyId:
				exists = True
				break
		if not exists:
			showMessage('Error', 'Invalid pair: employee and project')
			return
		if self.rec:
			self.editRecord()
		else:
			self.addRecord()

class ChangeRecordTasks(ChangeRecord):
	def __init__(self, parent, tableName, keys = None):
		super(ChangeRecordTasks, self).__init__(parent, tableName, keys)

	def createEdits(self):
		super(ChangeRecordTasks, self).createEdits()
		label = QtGui.QLabel(self)
		label.setText('Finished')
		self.gbox.addWidget(label, 4, 3)
		self.checkBox = QtGui.QCheckBox(self)
		self.gbox.addWidget(self.checkBox, 4, 4)

	def getValues(self):
		super(ChangeRecordTasks, self).getValues()
		if not self.checkBox.isChecked():
			for i, val in enumerate(self.values):
				if val['name'] == 'completionDate':
					val['value'] = None
	
	def checkCorrectness(self):
		if not self.editsAreNotEmpty():
			showMessage('Error', 'Fields must not be empty')
			return
		if self.rec and self.checkBox.isChecked():
			if len(dbi.query(TasksDependency, Task).filter(TasksDependency.slaveId == 
				self.rec.id).filter(Task.id == TasksDependency.masterId).filter(Task.completionDate is 
				None).all()):
				showMessage('Error', 'There are unfinished task dependencies')
				return
		if self.rec:
			self.editRecord()
		else:
			self.addRecord()

class ChangeRecordJobs(ChangeRecord):
	def __init__(self, parent, tableName, keys = None):
		super(ChangeRecordJobs, self).__init__(parent, tableName, keys)

	def createEdits(self):
		super(ChangeRecordJobs, self).createEdits()
		label = QtGui.QLabel(self)
		label.setText('Finished')
		self.gbox.addWidget(label, 4, 3)
		self.checkBox = QtGui.QCheckBox(self)
		self.gbox.addWidget(self.checkBox, 4, 4)

	def getValues(self):
		super(ChangeRecordJobs, self).getValues()
		if not self.checkBox.isChecked():
			for i, val in enumerate(self.values):
				if val['name'] == 'completionDate':
					val['value'] = None
	
	def checkCorrectness(self):
		if not self.editsAreNotEmpty():
			showMessage('Error', 'Fields must not be empty')
			return
		#something else?
		if self.rec:
			self.editRecord()
		else:
			self.addRecord()


class ChangeRecordTaskDependencies(ChangeRecord):
	def __init__(self, parent, tableName, keys = None):
		super(ChangeRecordTaskDependencies, self).__init__(parent, tableName, keys)

	def checkCorrectness(self):
		if not self.editsAreNotEmpty():
			showMessage('Error', 'Fields must not be empty')
			return
		self.getValues()
		masterId = self.values[0]['value']
		slaveId = self.values[1]['value']
		project1 = appInst.getProjectByTask(masterId)
		project2 = appInst.getProjectByTask(slaveId)
		if project1.id != project2.id:
			showMessage('Error', 'Chosen tasks must belong to the same project')
			return
		if masterId == slaveId:
			showMessage('Error', 'Chosen tasks must be different')
			return
		graph = appInst.getTasksDependency()
		print graph
		if self.rec:
			self.editRecord()
		else:
			self.addRecord()

class ViewTables(QtGui.QWidget):
	def __init__(self, parent, tableName):
		super(ViewTables, self).__init__(parent)

		self.ui = Ui_ViewTables()
		self.ui.setupUi(self)

		self.ui.addRecordButton.clicked.connect(self.addRecord)
		self.ui.editRecordButton.clicked.connect(self.editRecord)
		self.ui.deleteRecordButton.clicked.connect(self.deleteRecord)
		self.ui.tableWidget.itemSelectionChanged.connect(self.disableButtons)
		#app.mainWindow.loginDialog.loginSignal.connect(self.disableButtons)
		self.tableName = tableName
		self.setWindowTitle(tableName)
		appInst.tables.append(self)
		self.fillHeaders()
		self.fillCells()
		self.disableButtons()

	def fillHeaders(self):
		self.headers = appInst.getHeadersWithForeignValues(self.tableName)
		self.ui.tableWidget.setColumnCount(len(self.headers))
		self.ui.tableWidget.verticalHeader().setVisible(False)
		self.ui.tableWidget.setHorizontalHeaderLabels(self.headers)
		if not (appInst.curUser and appInst.curUser.canUpdate(self.tableName)):
			self.ui.addRecordButton.setDisabled(True)

	def fillCells(self):
		print self.tableName
		self.ui.tableWidget.clearContents()
		fields = appInst.getVisibleHeaders(appInst.getTable(self.tableName))
		values = appInst.selectAllWithForeignValues(self.tableName)
		print values
		self.ui.tableWidget.setRowCount(len(values))
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
		disable = not (appInst.curUser.admin and len(self.ui.tableWidget.selectedItems()))
		self.ui.addRecordButton.setDisabled(not appInst.curUser.admin)
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
			appInst.curUser.delete(self.tableName, self.primaryKeys[row])
			appInst.updateTableViews()

	def closeEvent(self, event):
		appInst.tables.remove(self)
		event.accept()

class ViewTableCompanies(ViewTables):
	def __init__(self, parent):
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
		self.ui.deleteRecordButton.setDisabled(self.primaryKeys[row] == 1)

class ViewTableUsers(ViewTables):
	def __init__(self, parent):
		super(ViewTableUsers, self).__init__(parent, 'users')

	def addRecord(self):
		rec = ChangeRecordUsers(self, self.tableName)
		rec.open()

	def editRecord(self):
		row = self.ui.tableWidget.currentRow()
		rec = ChangeRecordUsers(self, self.tableName, self.primaryKeys[row])
		rec.open()

	def disableButtons(self):
		self.ui.addRecordButton.setDisabled(not appInst.curUser.admin)
		disable = not (appInst.curUser.admin and len(self.ui.tableWidget.selectedItems()))
		if len(self.ui.tableWidget.selectedItems()):
			row = self.ui.tableWidget.currentRow()
			user = appInst.curUser.getRecord('users', self.primaryKeys[row])
			disable = user.login != appInst.curUser.login and not appInst.curUser.admin
		
		self.ui.editRecordButton.setDisabled(disable)
		disable = disable or len(appInst.getAdmins()) == 1
		self.ui.deleteRecordButton.setDisabled(disable)

class ViewTableEmployees(ViewTables):
	def __init__(self, parent):
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
		row = self.ui.tableWidget.currentRow()
		disable = not(appInst.hasProjects() and appInst.hasPartners())
		self.ui.deleteRecordButton.setDisabled(disable)

class ViewTableProjectEmployees(ViewTables):
	def __init__(self, parent):
		super(ViewTableProjectEmployees, self).__init__(parent, 'projectEmployees')

	def addRecord(self):
		rec = ChangeRecordProjectEmployees(self, self.tableName)
		rec.open()

	def editRecord(self):
		row = self.ui.tableWidget.currentRow()
		rec = ChangeRecordProjectEmployees(self, self.tableName, self.primaryKeys[row])
		rec.open()

	def disableButtons(self):
		canAdd = appInst.curUser.admin or appInst.currUser.isManager()
		self.ui.addRecordButton.setDisabled(not canAdd)
		canChange = appInst.curUser.admin
		if len(self.ui.tableWidget.selectedItems()):
			row = self.ui.tableWidget.currentRow()
			projectEmpolyee = appInst.curUser.getRecord('projectEmployees', self.primaryKeys[row])
			canChange = canChange or appInst.currUser.isManagerOnProject(projectEmpolyee.projectId)
		self.ui.editRecordButton.setDisabled(not canChange)
		self.ui.deleteRecordButton.setDisabled(not canChange)

class ViewTableTasks(ViewTables):
	def __init__(self, parent):
		super(ViewTableTasks, self).__init__(parent, 'tasks')

	def addRecord(self):
		rec = ChangeRecordTasks(self, self.tableName)
		rec.open()

	def editRecord(self):
		row = self.ui.tableWidget.currentRow()
		rec = ChangeRecordTasks(self, self.tableName, self.primaryKeys[row])
		rec.open()

	def disableButtons(self):
		canAdd = appInst.curUser.admin or appInst.currUser.isManager()
		self.ui.addRecordButton.setDisabled(not canAdd)
		canChange = appInst.curUser.admin
		if len(self.ui.tableWidget.selectedItems()):
			row = self.ui.tableWidget.currentRow()
			task = appInst.curUser.getRecord('tasks', self.primaryKeys[row])
			canChange = canChange or appInst.currUser.isManagerOnProject(task.projectId) or\
				appInst.currUser.isTaskDeveloper(task.id)
		self.ui.editRecordButton.setDisabled(not canChange)
		self.ui.deleteRecordButton.setDisabled(not canChange)


class ViewTableJobs(ViewTables):
	def __init__(self, parent):
		super(ViewTableJobs, self).__init__(parent, 'jobs')

	def addRecord(self):
		rec = ChangeRecordJobs(self, self.tableName)
		rec.open()

	def editRecord(self):
		row = self.ui.tableWidget.currentRow()
		rec = ChangeRecordJobs(self, self.tableName, self.primaryKeys[row])
		rec.open()

	def disableButtons(self):
		canAdd = appInst.curUser.admin or appInst.currUser.isManager() or\
			appInst.currUser.isDeveloper()
		self.ui.addRecordButton.setDisabled(not canAdd)
		canChange = appInst.curUser.admin
		if len(self.ui.tableWidget.selectedItems()):
			row = self.ui.tableWidget.currentRow()
			job = appInst.curUser.getRecord('jobs', self.primaryKeys[row])
			canChange = canChange or appInst.currUser.isManagerOnProject(job.task.projectId) or\
				appInst.currUser.isTaskDeveloper(job.task.id)
		self.ui.editRecordButton.setDisabled(not canChange)
		self.ui.deleteRecordButton.setDisabled(not canChange)


class ViewTableTaskDependencies(ViewTables):
	def __init__(self, parent):
		super(ViewTableTaskDependencies, self).__init__(parent, 'tasksDependencies')

	def addRecord(self):
		rec = ChangeRecordTaskDependencies(self, self.tableName)
		rec.open()

	def editRecord(self):
		row = self.ui.tableWidget.currentRow()
		rec = ChangeRecordTaskDependencies(self, self.tableName, self.primaryKeys[row])
		rec.open()

	def disableButtons(self):
		canAdd = appInst.curUser.admin and appInst.getMaxTasksNumOnProjects()> 1 or\
			appInst.currUser.isManager() and appInst.getMaxTasksNumOnProjectsWithManager() > 1
		self.ui.addRecordButton.setDisabled(not canAdd)
		canChange = appInst.curUser.admin
		if len(self.ui.tableWidget.selectedItems()):
			row = self.ui.tableWidget.currentRow()
			taskDependency = appInst.curUser.getRecord('tasksDependencies', self.primaryKeys[row])
			project1 = appInst.getProjectByTask(taskDependency.masterId)
			project2 = appInst.getProjectByTask(taskDependency.slaveId)
			canChange = canChange or (appInst.currUser.isManagerOnProject(project1.id) and\
				project1.id == project2.id)
		self.ui.editRecordButton.setDisabled(not canChange)
		self.ui.deleteRecordButton.setDisabled(not canChange)

