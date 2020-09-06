from pydoc import locate

from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget, QComboBox, QFormLayout

from . import __classes__, __config__
from .dataview import DataView


class ViewPanel(DataView):
    def __init__(self, workbench, parent: QWidget = None):
        super().__init__(workbench, parent)
        self.__currentFrameName: str = None
        self.__chartTypeCB = QComboBox(self)
        self.fLayout = QFormLayout(self)
        self.fLayout.addRow(__config__['description'], self.__chartTypeCB)
        moduleNames = __classes__.keys()
        self.fLayout.setHorizontalSpacing(40)
        self.__chartTypeCB.addItems(list(moduleNames))
        defaultSelection = __config__['default']
        self.__chartTypeCB.setCurrentText(defaultSelection)
        self.chartSelectionChanged(defaultSelection)
        self.__chartTypeCB.currentTextChanged.connect(self.chartSelectionChanged)

    @Slot(str)
    def chartSelectionChanged(self, text: str) -> None:
        if self.fLayout.rowCount() == 2:
            self.fLayout.removeRow(1)
        widget: type = locate(__classes__[text])  # subclass of DataView
        self.fLayout.addRow(widget(self._workbench, self))
        self.onFrameSelectionChanged(self.__currentFrameName, '')

    @Slot(str, str)
    def onFrameSelectionChanged(self, name: str, oldName: str) -> None:
        self.__currentFrameName = name
        self.fLayout.itemAt(1, QFormLayout.SpanningRole).widget().onFrameSelectionChanged(name, oldName)
