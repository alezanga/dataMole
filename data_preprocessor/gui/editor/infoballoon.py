from PySide2.QtCore import Qt
from PySide2.QtWidgets import QWidget, QLabel, QPushButton, QSizePolicy, QFrame, QVBoxLayout, \
    QTextBrowser


class InfoBalloon(QFrame):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle('Operation helper')
        self.body = QTextBrowser(self)
        # self.body.setWordWrap(True)
        # self.body.setTextFormat(Qt.RichText)
        closeButton = QPushButton('Close', self)
        self.body.setBackgroundRole(QLabel().backgroundRole())
        self.setWindowFlags(Qt.Tool)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.body.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.setMaximumWidth(400)
        closeButton.clicked.connect(self.close)
        layout = QVBoxLayout(self)
        layout.addWidget(self.body)
        layout.addWidget(closeButton, 0, Qt.AlignHCenter)

    def setText(self, text: str) -> None:
        self.body.setHtml(text)
