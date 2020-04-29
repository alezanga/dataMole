from PySide2.QtWidgets import QMainWindow, QMenuBar, QAction

from .MainWidget import MainWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        central_w = MainWidget()
        self.setCentralWidget(central_w)

        menu_bar = QMenuBar()
        menu_bar_file = menu_bar.addMenu('File')
        add_action = QAction('Add frame', menu_bar_file)
        add_action.setStatusTip('Create an empty dataframe in the workbench')
        add_action.triggered.connect(central_w.workbench_model.appendRow)
        menu_bar_file.addAction(add_action)
        menu_bar_file.show()

        self.setMenuBar(menu_bar)
