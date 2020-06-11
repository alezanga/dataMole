import sys

from PySide2 import QtCore
from PySide2.QtWidgets import QApplication

import data_preprocessor.logger as logger

if __name__ == "__main__":
    # Set up logger, QApp
    print('Python', sys.version)
    app = QApplication([])
    logger.setUpAppLogger()
    QtCore.qInstallMessageHandler(logger.qtMessageHandler)

    # Show main window
    from data_preprocessor.gui.main import MainWindow

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
