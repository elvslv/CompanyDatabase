import sqlalchemy
from design_files.widget_table import Ui_ViewTables
from main import appInst
from sqlalchemy import *
from Utils import *
from misc import *
from PyQt4 import QtGui, QtCore

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
	
	def addRecord(self):
		values = list()
		for i, edit in enumerate(self.edits):
			values.append({'name': edit.field, 'value': self.getValue(edit)})
		appInst.curUser.insert(self.table, values)
		try:
			self.tableView.fillCells()
		except:
			pass
		if self.edits[0].field == 'login':
			print 'kjgfkjksdh'
			self.tableView.addUserSignal.emit(values[0]['value'])
		self.close()

	def editRecord(self):
		values = dict()
		for i, edit in enumerate(self.edits):
			values[edit.field] = self.getValue(edit)
		appInst.curUser.update(self.table, self.keys, values)
		self.tableView.fillCells()
		self.close()
		
class ChangeRecordCompany(ChangeRecord):
	def __init__(self, parent, tableName, keys = None):
		super(ChangeRecordCompany, self).__init__(parent, tableName, keys)
		
	def checkCorrectness(self):
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
		
	def checkCorrectness(self):
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
		correct = True
		for edit in self.edits:
			if edit.field == 'name':
				correct = correct and len(edit.text()) > 0
			elif edit.field == 'login':
				correct = correct and len(edit.text()) > 0
		if not correct:
			showMessage('Error', 'Name must not be empty, each employee must be a user')
			return False
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
		print 'addedUser', login
		self.edits[-1].setText(login)
		
class ViewTables(QtGui.QWidget):
	def __init__(self, parent, tableName):
		super(ViewTables, self).__init__(parent)

		self.ui = Ui_ViewTables()
		self.ui.setupUi(self)

		self.ui.addRecordButton.clicked.connect(self.addRecord)
		self.ui.tableWidget.cellDoubleClicked.connect(self.editRecord)
		self.tableName = tableName
		self.setWindowTitle(tableName)

		self.fillHeaders()
		self.fillCells()

	def fillHeaders(self):
		self.headers = appInst.getHeadersWithForeignValues(self.tableName)
		self.ui.tableWidget.setColumnCount(len(self.headers))
		self.ui.tableWidget.verticalHeader().setVisible(False)
		self.ui.tableWidget.setHorizontalHeaderLabels(self.headers)
		if not (appInst.curUser and appInst.curUser.canUpdate(self.tableName)):
			self.ui.addRecordButton.setDisabled(True)

	def fillCells(self):
		self.ui.tableWidget.clearContents()
		fields = appInst.getVisibleHeaders(appInst.getTable(self.tableName))
		values = appInst.selectAllWithForeignValues(self.tableName)
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
		
	def addRecord(self):
		rec = ChangeRecord(self, self.tableName)
		rec.open()

	def editRecord(self, row, column):
		rec = ChangeRecord(self, self.tableName, self.primaryKeys[row])
		rec.open()

class ViewTableCompanies(ViewTables):
	def __init__(self, parent):
		super(ViewTableCompanies, self).__init__(parent, 'companies')

	def addRecord(self):
		rec = ChangeRecordCompany(self, self.tableName)
		rec.open()

	def editRecord(self, row, column):
		rec = ChangeRecordCompany(self, self.tableName, self.primaryKeys[row])
		rec.open()

class ViewTableUsers(ViewTables):
	def __init__(self, parent):
		super(ViewTableUsers, self).__init__(parent, 'users')

	def addRecord(self):
		rec = ChangeRecordUsers(self, self.tableName)
		rec.open()

	def editRecord(self, row, column):
		rec = ChangeRecordUsers(self, self.tableName, self.primaryKeys[row])
		rec.open()

class ViewTableEmployees(ViewTables):
	def __init__(self, parent):
		super(ViewTableEmployees, self).__init__(parent, 'employees')

	def addRecord(self):
		rec = ChangeRecordEmployees(self, self.tableName)
		rec.open()

	def editRecord(self, row, column):
		rec = ChangeRecordEmployees(self, self.tableName, self.primaryKeys[row])
		rec.open()
