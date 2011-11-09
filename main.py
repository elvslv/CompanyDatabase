import sys
import os

from PyQt4 import QtGui, QtCore

from design_files.window_main import Ui_MainWindow
from design_files.dialog_about import Ui_AboutDialog

class AboutDialog(QtGui.QDialog):
    def __init__(self, parent):
        super(AboutDialog, self).__init__(parent)

        self.ui = Ui_AboutDialog()
        self.ui.setupUi(self)

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.aboutDialog = AboutDialog(self)
		
        self.ui.actionAbout.triggered.connect(self.aboutDialog.open)

class MainApplication(QtGui.QApplication):

    def exec_(self):
        self.mainwindow = MainWindow()
        self.mainwindow.showNormal()
        super(MainApplication, self).exec_()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    wind = MainWindow()
    wind.show()
    sys.exit(app.exec_())


