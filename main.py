# This Python file uses the following encoding: utf-8
import sys
from PySide2.QtWidgets import QApplication, QMainWindow

from data_preprocessor.gui.widget import PipelineWidget
from data_preprocessor.gui.generic.FramedPanel import frameDecorator


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    f = PipelineWidget
    window.setCentralWidget(f())
    window.show()
    sys.exit(app.exec_())
