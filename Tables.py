import sqlalchemy
from design_files.widget_table import Ui_ViewTables
from main import appInst
from sqlalchemy import *
from Utils import showMessage

from PyQt4 import QtGui, QtCore

class ChangeRecord(QtGui.QDialog):
	def __init__(self, parent, tableName, exists = False, keys = None):
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
		if exists:
			self.rec = appInst.curUser.getRecord(tableName, keys)

		row = 0
		self.edits = []
		for field in self.fields:
			label = QtGui.QLabel(self)
			label.setText(field.name)
			self.gbox.addWidget(label, row, 0, 1, 1)
			edit = self.getEdit(field, self.rec[field.name] if self.rec else None)
			self.edits.append(edit)
			self.gbox.addWidget(edit, row, 1, 1, 1)
			row += 1
			
		self.gbox.addWidget(self.buttonBox, row, 1, 1, 1)
		self.setLayout(self.gbox)
		
		self.buttonBox.accepted.connect(self.checkCorrectness)
		self.buttonBox.rejected.connect(self.reject)

	def getEdit(self, field, val):
		if field.foreign_keys:
			return self.createComboBox(field, val)
		if isinstance(field.type, Boolean):
			return self.createCheckBox(field, val)
		if isinstance(field.type, DateTime):
			return self.createDateTimeEdit(field, val)
		if isinstance(field.type, String) or isinstance(field.type, Text):
			return self.createLineEdit(field, val)
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
		items = appInst.curUser.getForeignValues(self.table, field)
		for i, item in enumerate(items):
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
		self.addRecord()

	def getValue(self, edit):
		if isinstance(edit, QtGui.QSpinBox):
			return edit.value()
		if isinstance(edit, QtGui.QLineEdit):
			return edit.text()
		if isinstance(edit, QtGui.QComboBox):
			val = edit.itemData(edit.currentIndex())
			if val is None:
				return edit.currentText()
			return val
		if isinstance(edit, QtGui.QCheckBox):
			return edit.isChecked()
		##todo: datetimeedit
		showMessage('Error', 'Unknown edit type')
	
	def addRecord(self):
		values = list()
		for i, edit in enumerate(self.edits):
			values.append(self.getValue(edit))
		appInst.curUser.insert(self.table, values)
		self.tableView.fillCells()
		self.close()
		showMessage('EEE', 'added')

class ChangeProject(ChangeRecord):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def createIntegerBox(self, field, val):
		if field.name != 'stage':
			return super().createIntegerBox(field, val)
		result = QtGui.QComboBox(self)
		stages = ['project is not started', 'project is started', 'project is finished']
		
		for i, item in enumerate(stages):
			result.addItem(item, i)
			if val is not None and i == val:
				result.setIndex(i)
		return result

class ChangeContract(ChangeRecord):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def createIntegerBox(self, field, val):
		if field.name != 'activity':
			return super().createIntegerBox(field, val)
		result = QtGui.QComboBox(self)
		activities = ['contract is not made', 'contract is made', 'contract is terminated',
			'contract is finished']
		
		for i, item in enumerate(activities):
			result.addItem(item, i)
			if val is not None and i == val:
				result.setIndex(i)
		return result

class ChangeProjectEmployee(ChangeRecord):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def createIntegerBox(self, field, val):
		if field.name != 'role':
			return super().createIntegerBox(field, val)
		result = QtGui.QComboBox(self)
		activities = ['developer', 'manager']
		
		for i, item in enumerate(activities):
			result.addItem(item, i)
			if val is not None and i == val:
				result.setIndex(i)
		return result

		
class ViewTables(QtGui.QWidget):
	def __init__(self, parent, tableName):
		super(ViewTables, self).__init__(parent)

		self.ui = Ui_ViewTables()
		self.ui.setupUi(self)

		self.ui.addRecordButton.clicked.connect(self.addRecord)

		self.tableName = tableName
		self.setWindowTitle(tableName)

		self.fillHeaders()
		self.fillCells()

	def fillHeaders(self):
		self.headers = appInst.getHeaders(self.tableName)
		self.ui.tableWidget.setColumnCount(len(self.headers))
		self.ui.tableWidget.setHorizontalHeaderLabels(self.headers)
		if not (appInst.curUser and appInst.curUser.canUpdate(self.tableName)):
			self.ui.addRecordButton.setDisabled(True)

	def fillCells(self):
		self.ui.tableWidget.clearContents()
		values = appInst.selectAll(self.tableName)
		self.ui.tableWidget.setRowCount(len(values))
		row = -1
		for value in values:
			row = row + 1
			column = -1
			for item in value:
				column = column + 1
				newitem = QtGui.QTableWidgetItem(item)
				self.ui.tableWidget.setItem(row, column, newitem)

	def addRecord(self):
		rec = ChangeRecord(self, self.tableName)
		rec.open()
