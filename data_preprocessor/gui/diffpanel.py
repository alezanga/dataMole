import sys

from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget, QTableView, QSplitter, QHBoxLayout, QComboBox, QVBoxLayout

from data_preprocessor.gui.mainmodels import IncrementalRenderFrameModel
from data_preprocessor.gui.workbench import WorkbenchModel


class DataframeView(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.inputCB = QComboBox(self)
        self.dataView = QTableView(self)
        layout.addWidget(self.inputCB)
        layout.addWidget(self.dataView)
        self._workbench: WorkbenchModel = None

    def setWorkbench(self, w: WorkbenchModel) -> None:
        self.inputCB.setModel(w)
        self._workbench = w
        self.inputCB.currentTextChanged.connect(self.setDataframe)

    @Slot(str)
    def setDataframe(self, name: str) -> None:
        if not self.dataView.model():
            self.dataView.setModel(IncrementalRenderFrameModel(parent=self))
            self.dataView.horizontalScrollBar().valueChanged.connect(self.onHorizontalScroll)
            self.dataView.verticalScrollBar().valueChanged.connect(self.onVerticalScroll)
        frameModel = self._workbench.getDataframeModelByName(name)
        self.dataView.model().setSourceModel(frameModel)

    @Slot(int)
    def onVerticalScroll(self, *_) -> None:
        self.dataView.model().setScrollMode('row')

    @Slot(int)
    def onHorizontalScroll(self, *_) -> None:
        self.dataView.model().setScrollMode('column')


class DataframeDiffView(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.dataWidgetL = DataframeView(self)
        self.dataWidgetR = DataframeView(self)

        splitter = QSplitter(self)
        splitter.addWidget(self.dataWidgetL)
        splitter.addWidget(self.dataWidgetR)
        layout = QHBoxLayout(self)
        layout.addWidget(splitter)
        splitter.setSizes([sys.maxsize, sys.maxsize])

        self.dataWidgetL.dataView.verticalScrollBar().valueChanged.connect(
            self.dataWidgetR.dataView.verticalScrollBar().setValue)
        self.dataWidgetR.dataView.verticalScrollBar().valueChanged.connect(
            self.dataWidgetL.dataView.verticalScrollBar().setValue)
        self.dataWidgetL.dataView.horizontalScrollBar().valueChanged.connect(
            self.dataWidgetR.dataView.horizontalScrollBar().setValue)
        self.dataWidgetR.dataView.horizontalScrollBar().valueChanged.connect(
            self.dataWidgetL.dataView.horizontalScrollBar().setValue)
