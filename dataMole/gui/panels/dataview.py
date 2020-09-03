from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget


class DataView(QWidget):
    """ An interface to use with data views to be shown in the View panel """

    def __init__(self, workbench, parent=None):
        super().__init__(parent)
        self._workbench = workbench

    @Slot(str, str)
    def onFrameSelectionChanged(self, name: str, oldName: str) -> None:
        """ React to the change of the active frame """
        pass
