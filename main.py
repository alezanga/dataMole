import sys

from PySide2 import QtCore
from PySide2.QtWidgets import QApplication

from data_preprocessor import flogging

if __name__ == "__main__":
    # Set up logger, QApp
    print('Python', sys.version)
    app = QApplication([])
    flogging.setUpRootLogger()
    rootFmt = '%(asctime)s:%(levelname)s:%(module)s.%(funcName)s:%(lineno)d:%(message)s'
    flogging.setUpLogger(name='app', folder='app', fmt=rootFmt, level=flogging.LEVEL)
    flogging.setUpLogger(name='ops', folder='operations', fmt='%(message)s', level=flogging.INFO)
    QtCore.qInstallMessageHandler(flogging.qtMessageHandler)

    # Initialize globals and mainWindow
    from data_preprocessor import gui

    mw = gui.widgets.window.MainWindow()
    # Create status bar
    gui.statusBar = gui.widgets.statusbar.StatusBar(mw)
    mw.setStatusBar(gui.statusBar)
    gui.notifier = gui.widgets.notifications.Notifier(mw)
    # Set notifier in main window for update
    mw.notifier = gui.notifier
    gui.notifier.mNotifier.updatePosition()
    mw.show()
    sys.exit(app.exec_())
