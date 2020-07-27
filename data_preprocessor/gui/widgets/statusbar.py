from PySide2.QtCore import Slot, QUrl, QSize
from PySide2.QtGui import QDesktopServices
from PySide2.QtWidgets import QStatusBar, QWidget, QLabel

from data_preprocessor.gui.widgets.waitingspinnerwidget import QtWaitingSpinner


class StatusBar(QStatusBar):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        # logButton = QPushButton('Open log', self)
        self._spinner = QtWaitingSpinner(self, centerOnParent=False)
        self._spinner.setInnerRadius(6)
        self.setContentsMargins(5, 1, 5, 1)

        self.addPermanentWidget(self._spinner, 1)
        spacer = QLabel()
        spacer.setFixedSize(QSize(5, 5))
        self.addPermanentWidget(spacer, 0)
        # self.addPermanentWidget(logButton, 0)

        # logButton.pressed.connect(self._openLog)

    @Slot(str)
    def logMessage(self, msg: str) -> None:
        self.showMessage(msg, 10)

    @Slot()
    def startSpinner(self) -> None:
        self._spinner.start()

    @Slot()
    def stopSpinner(self) -> None:
        self._spinner.stop()

    @Slot()
    def _openLog(self) -> None:
        from data_preprocessor.flogging.utils import LOG_PATH
        QDesktopServices.openUrl(QUrl(LOG_PATH))
