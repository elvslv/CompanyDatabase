import sys
import os

from PyQt4 import QtGui, QtCore

from design_files.window_main import Ui_MainWindow
from design_files.dialog_about import Ui_AboutDialog
from design_files.dialog_login import Ui_LoginDialog
from design_files.add_admin_window import Ui_addAdminDialog

from DB.Db import dbi
from main import appInst
from DB.dbExceptions import DBException
from Utils import showMessage
from Tables import *
from misc import *

class MainApplication(QtGui.QApplication):
	def exec_(self):
		self.mainWindow = MainWindow()
		self.mainWindow.showNormal()
		super(MainApplication, self).exec_()

	@QtCore.pyqtSlot(str, str)
	def login(self, username, password):
		appInst.setCurUser(username, password)
		self.mainWindow.changeState('Hello, %s! %s' %(username, 
			"You're admin" if appInst.isAdmin() else ''))
		return appInst.curUser

	@QtCore.pyqtSlot()
	def updateTableViews(self):
		for w in app.mainWindow.ui.mdiArea.subWindowList():
			w.widget().fillCells()

app = MainApplication(sys.argv)

class AboutDialog(QtGui.QDialog):
	def __init__(self, parent):
		super(AboutDialog, self).__init__(parent)

		self.ui = Ui_AboutDialog()
		self.ui.setupUi(self)

class AddAdminDialog(QtGui.QDialog):
	def __init__(self, parent):
		super(AddAdminDialog, self).__init__(parent)

		self.ui = Ui_addAdminDialog()
		self.ui.setupUi(self)

		self.ui.buttonBox.button(QtGui.QDialogButtonBox.Ok).setDisabled(True)
		self.ui.adminPasswordEdit.textChanged.connect(self.checkForEmpty)
		self.ui.adminUsernameEdit.textChanged.connect(self.checkForEmpty)
		self.ui.companyNameEdit.textChanged.connect(self.checkForEmpty)
		self.ui.companyDetailsEdit.textChanged.connect(self.checkForEmpty)
		
		self.accepted.connect(self.addAdmin)

	def checkForEmpty(self):
		disable = len(self.ui.adminPasswordEdit.text()) < MIN_PASSWORD_LENGTH or\
			len(self.ui.adminUsernameEdit.text()) < MIN_LOGIN_LENGTH or\
			len(self.ui.companyNameEdit.text()) < 1 or len(self.ui.companyDetailsEdit.text()) < 1 
		self.ui.buttonBox.button(QtGui.QDialogButtonBox.Ok).setDisabled(disable)

	def addAdmin(self):
		appInst.addUser(self.ui.adminUsernameEdit.text(), self.ui.adminPasswordEdit.text(), 
			True)
		appInst.addCompany(self.ui.companyNameEdit.text(), self.ui.companyDetailsEdit.text())

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
	def showTableTrigger(self, tableName, param = None):
		return lambda: self.showTable(tableName) if not param else lambda: self.showTable(tableName, param)
		
	def __init__(self):
		super(MainWindow, self).__init__()

		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)

		self.aboutDialog = AboutDialog(self)
		self.loginDialog = LoginDialog(self)
		self.addAdminDialog = AddAdminDialog(self)

		self.ui.actionAbout.triggered.connect(self.aboutDialog.open)
		self.ui.actionLogin.triggered.connect(self.loginDialog.open)
		
		self.ui.actionViewCompanies.triggered.connect(self.showTableTrigger('companies'))
		self.ui.actionViewUsers.triggered.connect(self.showTableTrigger('users'))
		self.ui.actionViewEmployees.triggered.connect(self.showTableTrigger('employees'))
		self.ui.actionViewProjects.triggered.connect(self.showTableTrigger('projects'))
		self.ui.actionViewContracts.triggered.connect(self.showTableTrigger('contracts'))
		self.ui.actionViewProjectEmployees.triggered.connect(self.showTableTrigger('projectEmployees'))
		self.ui.actionViewTasks.triggered.connect(self.showTableTrigger('tasks'))
		self.ui.actionViewJobs.triggered.connect(self.showTableTrigger('jobs'))
		self.ui.actionViewTasksDependencies.triggered.connect(self.showTableTrigger('tasksDependencies'))
		self.ui.actionJobs.triggered.connect(self.showTableTrigger('jobs', True))
		
		self.loginDialog.loginSignal.connect(app.login)

		if not len(appInst.getAdmins()):
			self.addAdminDialog.open()

	def changeState(self, state):
		self.ui.curStateLabel.setText(state)

	def showTable(self, tableName, param = None):
		if tableName == 'companies':
			table = ViewTableCompanies(self)
		elif tableName == 'users':
			table = ViewTableUsers(self)
		elif tableName == 'employees':
			table = ViewTableEmployees(self)
		elif tableName == 'projects':
			table = ViewTableProjects(self)
		elif tableName == 'contracts':
			table = ViewTableContracts(self)
		elif tableName == 'projectEmployees':
			table = ViewTableProjectEmployees(self)
		elif tableName == 'tasks':
			table = ViewTableTasks(self)
		elif tableName == 'jobs':
			table = ViewTableJobs(self, param)
		elif tableName == 'tasksDependencies':
			table = ViewTableTaskDependencies(self)
		else:
			table = ViewTables(self, tableName)
		self.ui.mdiArea.addSubWindow(table)
		table.show()
	
if __name__ == '__main__':
	sys.exit(app.exec_())

