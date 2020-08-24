from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget, QTableView, QSplitter, QHBoxLayout, QComboBox, QVBoxLayout, \
    QPushButton, QCheckBox, QScrollBar

from data_preprocessor.data import Frame
from data_preprocessor.gui.mainmodels import IncrementalRenderFrameModel, SearchableAttributeTableWidget, \
    FrameModel
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
        # Get frame model and set it in the table
        frameModel = self._workbench.getDataframeModelByName(name)
        self.dataView.model().setSourceModel(frameModel)

    @Slot(int)
    def onVerticalScroll(self, *_) -> None:
        self.dataView.model().setScrollMode('row')

    @Slot(int)
    def onHorizontalScroll(self, *_) -> None:
        self.dataView.model().setScrollMode('column')


class DataframeSideBySideView(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.dataWidgetL = DataframeView(self)
        self.dataWidgetR = DataframeView(self)
        self.scrollTogetherH = QCheckBox('Lock horizontal scroll', self)
        self.scrollTogetherV = QCheckBox('Lock vertical scroll', self)
        cLayout = QHBoxLayout()
        cLayout.addWidget(self.scrollTogetherH)
        cLayout.addWidget(self.scrollTogetherV)

        splitter = QSplitter(self)
        splitter.addWidget(self.dataWidgetL)
        splitter.addWidget(self.dataWidgetR)
        layout = QVBoxLayout(self)
        layout.addLayout(cLayout)
        layout.addWidget(splitter)
        splitter.setSizes([10, 10])

        self.scrollTogetherH.toggled.connect(self.lockScrollChangedHorizontal)
        self.scrollTogetherV.toggled.connect(self.lockScrollChangedVertical)

    @Slot(bool)
    def lockScrollChangedVertical(self, checked: bool) -> None:
        self._connectScroll(self.dataWidgetL.dataView.verticalScrollBar(),
                            self.dataWidgetR.dataView.verticalScrollBar(), checked)

    @Slot(bool)
    def lockScrollChangedHorizontal(self, checked: bool) -> None:
        self._connectScroll(self.dataWidgetL.dataView.horizontalScrollBar(),
                            self.dataWidgetR.dataView.horizontalScrollBar(), checked)

    @staticmethod
    def _connectScroll(scroll1: QScrollBar, scroll2: QScrollBar, connect: bool) -> None:
        if connect:
            scroll1.valueChanged.connect(scroll2.setValue)
            scroll1.valueChanged.connect(scroll2.setValue)
            scroll2.valueChanged.connect(scroll1.setValue)
            scroll2.valueChanged.connect(scroll1.setValue)
        else:
            scroll1.valueChanged.disconnect(scroll2.setValue)
            scroll1.valueChanged.disconnect(scroll2.setValue)
            scroll2.valueChanged.disconnect(scroll1.setValue)
            scroll2.valueChanged.disconnect(scroll1.setValue)


class DiffDataframeWidget(QWidget):
    # NOTE: NOT USED FOR NOW
    def __init__(self, parent=None):
        super().__init__(parent)
        self._workbench: WorkbenchModel = None

        sideWidget = QWidget(self)
        sideLayout = QVBoxLayout()
        self.CBL = QComboBox(sideWidget)
        self.CBR = QComboBox(sideWidget)
        self.columnsL = SearchableAttributeTableWidget(sideWidget, True, showTypes=True)
        self.columnsR = SearchableAttributeTableWidget(sideWidget, True, showTypes=True)
        button = QPushButton('Compute diff', self)
        sideLayout.addWidget(self.CBL)
        sideLayout.addWidget(self.columnsL)
        sideLayout.addWidget(self.CBR)
        sideLayout.addWidget(self.columnsR)
        sideLayout.addWidget(button)
        sideWidget.setLayout(sideLayout)

        self.tableWidget = QTableView(self)

        splitter = QSplitter(self)
        splitter.addWidget(sideWidget)
        splitter.addWidget(self.tableWidget)

        layout = QHBoxLayout(self)
        layout.addWidget(splitter)

        self.CBL.currentTextChanged.connect(self.setAttributeModelL)
        self.CBR.currentTextChanged.connect(self.setAttributeModelR)
        button.clicked.connect(self.computeDiff)

    @Slot(str)
    def setAttributeModelL(self, name: str) -> None:
        frameModel = self._workbench.getDataframeModelByName(name)
        self.columnsL.setSourceFrameModel(frameModel)

    @Slot(str)
    def setAttributeModelR(self, name: str) -> None:
        frameModel = self._workbench.getDataframeModelByName(name)
        self.columnsR.setSourceFrameModel(frameModel)

    def setWorkbench(self, w: WorkbenchModel) -> None:
        self._workbench = w
        self.CBL.setModel(w)
        self.CBR.setModel(w)
        model = IncrementalRenderFrameModel(parent=self)
        frameModel = FrameModel(model)
        model.setSourceModel(frameModel)
        self.tableWidget.setModel(model)

    @Slot()
    def computeDiff(self) -> None:
        frame1 = self.columnsL.model().frameModel().frame.getRawFrame()
        frame2 = self.columnsR.model().frameModel().frame.getRawFrame()
        changedMask = frame1 != frame2
        diffRows = changedMask.any(1)
        diffColumns = changedMask.any(0)
        frame = frame1.loc[diffRows, diffColumns]
        self.tableWidget.model().sourceModel().setFrame(Frame(frame))
