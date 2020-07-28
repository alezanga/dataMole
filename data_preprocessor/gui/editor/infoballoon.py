from PySide2.QtCore import Qt
from PySide2.QtWidgets import QWidget, QLabel, QPushButton, QSizePolicy, QFrame, QVBoxLayout, \
    QTextBrowser


class InfoBalloon(QFrame):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle('Operation helper')
        self.body = QTextBrowser(self)
        closeButton = QPushButton('Close', self)
        self.body.setBackgroundRole(QLabel().backgroundRole())
        self.setWindowFlags(Qt.Tool)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.body.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.setMinimumWidth(500)
        self.setMaximumWidth(1000)
        closeButton.clicked.connect(self.close)
        layout = QVBoxLayout(self)
        layout.addWidget(self.body)
        layout.addWidget(closeButton, 0, Qt.AlignHCenter)

    def setText(self, text: str) -> None:
        self.body.setHtml(text)
        self.body.document().setTextWidth(500)
        self.body.document().adjustSize()
        self.resize(500, self.body.document().size().height())
