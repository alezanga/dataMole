import sys

from PySide2.QtWidgets import QApplication

from data_preprocessor.gui.window.MainWindow import MainWindow

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
