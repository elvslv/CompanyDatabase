from PyQt4 import QtGui

def showMessage(title, message):
	mbox = QtGui.QMessageBox(QtGui.QMessageBox.Critical, title,
		message, QtGui.QMessageBox.Ok)
	mbox.exec_()

def isEnum(field):
	return field.name in ('activity', 'stage', 'role')


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
	datetime = QtCore.QDateTime.currentDateTime() if val is None else QtCore.QDateTime.fromString(val, QtCore.Qt.ISODate)
	result = QtGui.QDateTimeEdit(datetime, parent)
	return result

def createComboBox(parent, field, val):
	result = QtGui.QComboBox(parent)
	if isEnum(field):
		items = globals()[field.name]
	else:
		items = appInst.getForeignValues(parent.table, field)
	for i, item in enumerate(items):
		if field.name in ('activity', 'stage', 'role'):
			result.addItem(item, i)
		else:
			result.addItem(item[1], item[0])
		if not(val == None) and (item[0] == val):
			result.setCurrentIndex(i)
	return result

def createCheckBox(parent, field, val):
	result = QtGui.QCheckBox(parent)
	if val is not None:
		result.setChecked(val == 1)
	return result