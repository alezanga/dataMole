from typing import Union, Optional

from PySide2.QtGui import QIcon, Qt, QPixmap
from PySide2.QtWidgets import QLabel, QWidget, QMessageBox, QStyle, QApplication, \
    QSizePolicy, QHBoxLayout


def getStandardIcon(icon: Union[QMessageBox.Icon, QStyle.StandardPixmap], size: int) -> QPixmap:
    style: QStyle = QApplication.style()
    tmpIcon: QIcon
    if icon == QMessageBox.Information or icon == QStyle.SP_MessageBoxInformation:
        tmpIcon = style.standardIcon(QStyle.SP_MessageBoxInformation, None, None)
    elif icon == QMessageBox.Warning or icon == QStyle.SP_MessageBoxWarning:
        tmpIcon = style.standardIcon(QStyle.SP_MessageBoxWarning, None, None)
    elif icon == QMessageBox.Critical or icon == QStyle.SP_MessageBoxCritical:
        tmpIcon = style.standardIcon(QStyle.SP_MessageBoxCritical, None, None)
    elif icon == QMessageBox.Question:
        tmpIcon = style.standardIcon(QStyle.SP_MessageBoxQuestion, None, None)
    else:
        tmpIcon = style.standardIcon(icon, None, None)
    if not tmpIcon.isNull():
        return tmpIcon.pixmap(size, size)
    return QPixmap()


class MessageLabel(QWidget):
    # WordWrap should be fixed
    def __init__(self, text: str, icon: Union[QMessageBox.Icon, QStyle.StandardPixmap, None] = None,
                 color: Optional[str] = None, parent: QWidget = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(0)
        if icon:
            size = 20
            iconLabel = QLabel(self)
            iconLabel.setContentsMargins(0, 0, 0, 0)
            iconLabel.setMargin(0)
            iconLabel.setPixmap(getStandardIcon(icon, size))
            iconLabel.setFixedSize(size, size)
            layout.addWidget(iconLabel, 1, Qt.AlignLeft | Qt.AlignVCenter)
            iconLabel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            layout.addSpacing(6)
        self._textLabel = QLabel(self)
        self._textLabel.setContentsMargins(0, 0, 0, 0)
        self._textLabel.setText(text)
        if color:
            self._textLabel.setStyleSheet('color: {}'.format(color))
        self._textLabel.setMargin(0)
        layout.addWidget(self._textLabel, 60, Qt.AlignLeft)
        self._textLabel.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        # self._textLabel.setWordWrap(True)

    def setText(self, text: str) -> None:
        self._textLabel.setText(text)

    def setTextColor(self, color: str) -> None:
        self._textLabel.setStyleSheet('color: {}'.format(color))

    def text(self) -> str:
        return self._textLabel.text()
