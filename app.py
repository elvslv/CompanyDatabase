import sys
import os

from PyQt4 import QtGui, QtCore

from design_files.window_main import Ui_MainWindow
from design_files.dialog_about import Ui_AboutDialog
from design_files.dialog_login import Ui_LoginDialog

from DB.Db import dbi
from main import appInst
from DB.dbExceptions import DBException

class MainApplication(QtGui.QApplication):
	def exec_(self):
		self.mainWindow = MainWindow()
		self.mainWindow.showNormal()
		super(MainApplication, self).exec_()

	@QtCore.pyqtSlot(str, str)
	def login(self, username, password):
		try:
			appInst.setCurUser(username, password)
			self.mainWindow.changeState('Hello, %s! %s' %(username, 
				"You're admin" if appInst.curUser.admin else ''))
			return appInst.curUser
		except DBException, e:
			self.showError('Invalid login or password')

	def showError(self, error):
		mbox = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error',
			error, QtGui.QMessageBox.Ok)
		mbox.exec_()

app = MainApplication(sys.argv)

class AboutDialog(QtGui.QDialog):
	def __init__(self, parent):
		super(AboutDialog, self).__init__(parent)

		self.ui = Ui_AboutDialog()
		self.ui.setupUi(self)

class LoginDialog(QtGui.QDialog):
	loginSignal = QtCore.pyqtSignal(str, str)
	
	def __init__(self, parent):
		super(LoginDialog, self).__init__(parent)

		self.ui = Ui_LoginDialog()
		self.ui.setupUi(self)

		self.accepted.connect(self.loginPressed)

	@QtCore.pyqtSlot()
	def loginPressed(self):
		self.loginSignal.emit(self.ui.usernameEdit.text(),
			self.ui.passwordEdit.text())

class MainWindow(QtGui.QMainWindow):
	def __init__(self):
		super(MainWindow, self).__init__()

		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)

		self.aboutDialog = AboutDialog(self)
		self.loginDialog = LoginDialog(self)

		self.ui.actionAbout.triggered.connect(self.aboutDialog.open)
		self.ui.actionLogin.triggered.connect(self.loginDialog.open)
		self.loginDialog.loginSignal.connect(app.login)

	def changeState(self, state):
		self.ui.curStateLabel.setText(state)
if __name__ == '__main__':
	sys.exit(app.exec_())

