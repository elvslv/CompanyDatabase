from PyQt4 import QtGui

def showMessage(title, message):
	mbox = QtGui.QMessageBox(QtGui.QMessageBox.Critical, title,
		message, QtGui.QMessageBox.Ok)
	mbox.exec_()
