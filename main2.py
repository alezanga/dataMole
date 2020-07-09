import sys

from PySide2 import QtCore
from PySide2.QtWidgets import QApplication

from data_preprocessor import flogging

if __name__ == "__main__":
    # Set up logger, QApp
    print('Python', sys.version)
    app = QApplication([])
    flogging.setUpAppLogger()
    flogging.setUpOperationLogger()
    QtCore.qInstallMessageHandler(flogging.qtMessageHandler)

    # Show main window
    from data_preprocessor.gui.main import MainWindow

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
