import sys
import os

from PyQt4 import QtGui, QtCore

from design_files.window_main import Ui_MainWindow
from design_files.dialog_about import Ui_AboutDialog
from design_files.dialog_login import Ui_LoginDialog
from design_files.add_admin_window import Ui_addAdminDialog
from design_files.gantt_dialog import Ui_ganttDialog

from DB.Db import dbi
from main import appInst
from DB.dbExceptions import DBException
from Utils import showMessage
from Tables import *
from misc import *
from plot import GanttChart
from sqlalchemy.exc import IntegrityError

class MainApplication(QtGui.QApplication):
	def exec_(self):
		self.mainWindow = MainWindow()
		self.mainWindow.showNormal()
		try:
			super(MainApplication, self).exec_()
		except IntegrityError:
			showMessage('Error', 'The same value already exists')
		except DBException, e: 
			showMessage('Error', e.value)

	def login(self, username, password):
		appInst.setCurUser(username, password)
		self.mainWindow.changeState('Hello, %s! %s' %(username, 
			"You're admin" if appInst.isAdmin() else ''))
		appInst.disableButtons()
		return appInst.curUser

	def logout(self):
		appInst.curUser = None
		appInst.disableButtons()
		self.mainWindow.changeState('Please login')

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

class GanttDialog(QtGui.QDialog):
	def __init__(self, parent):
		super(GanttDialog, self).__init__(parent)

		self.ui = Ui_ganttDialog()
		self.ui.setupUi(self)
		self.update()
		self.ui.generateBtn.clicked.connect(self.generateDiagram)

	def update(self):
		self.ui.projectsComboBox.clear()
		self.ui.webView.setHtml('<html><body></body></html>')
		projects = appInst.getNotEmptyProjects()
		for project in projects:
			self.ui.projectsComboBox.addItem(project.name, project.id)

	def generateDiagram(self):
		if not self.ui.projectsComboBox.currentText():
			raise DBException("There aren't projects in db")
			return
		projectId = self.ui.projectsComboBox.itemData(self.ui.projectsComboBox.currentIndex()).toInt()[0]
		ganttDiagram = GanttChart(dbi.query(Task).filter(Task.projectId == projectId).all())
		self.ui.webView.setHtml(ganttDiagram.generateDiagram())

class MainWindow(QtGui.QMainWindow):
	def showTableTrigger(self, tableName, param = None):
		return lambda: self.showTable(tableName, param)

	def showGanttDiagram(self):
		self.ganttDiagram.update()
		self.ganttDiagram.open()

	def __init__(self):
		super(MainWindow, self).__init__()

		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)

		self.aboutDialog = AboutDialog(self)
		self.loginDialog = LoginDialog(self)
		self.addAdminDialog = AddAdminDialog(self)
		self.ganttDiagram = GanttDialog(self)
		
		self.ui.actionAbout.triggered.connect(self.aboutDialog.open)
		self.ui.actionLogin.triggered.connect(self.openLoginDialog)
		self.ui.actionLogout.triggered.connect(self.logout)
		self.ui.actionLogout.setDisabled(True)
		self.ui.actionExit_2.triggered.connect(self.close)
		
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
		self.ui.actionGantt_diagram.triggered.connect(self.showGanttDiagram)
		self.loginDialog.loginSignal.connect(self.login)

		if not len(appInst.getAdmins()):
			self.addAdminDialog.open()

	def openLoginDialog(self):
		self.loginDialog.ui.usernameEdit.setText('')
		self.loginDialog.ui.passwordEdit.setText('')
		self.loginDialog.open()

	def logout(self):
		self.ui.actionLogin.setDisabled(False)
		self.ui.actionLogout.setDisabled(True)
		app.logout()
	
	@QtCore.pyqtSlot(str, str)
	def login(self, username, password):
		try:
			app.login(username, password)
			self.ui.actionLogin.setDisabled(True)
			self.ui.actionLogout.setDisabled(False)
		except NoResultFound:
			raise DBException('Invalid login or password')
		
	def changeState(self, state):
		self.ui.statusLabel.setText(state)

	def showTable(self, tableName, param):
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

