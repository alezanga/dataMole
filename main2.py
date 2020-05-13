import sys

from PySide2 import QtCore
from PySide2.QtWidgets import QApplication

import data_preprocessor.logger as logger
from data_preprocessor.gui.main import MainWindow

if __name__ == "__main__":
    logger.setUpLogger()
    QtCore.qInstallMessageHandler(logger.qtMessageHandler)
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
