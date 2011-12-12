from PyQt4 import QtGui

def showMessage(title, message):
	mbox = QtGui.QMessageBox(QtGui.QMessageBox.Critical, title,
		message, QtGui.QMessageBox.Ok)
	mbox.exec_()

def isEnum(field):
	return field.name in ('activity', 'role', 'state')