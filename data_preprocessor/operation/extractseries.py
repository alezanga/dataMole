from typing import Any, Dict, List, Tuple, Iterable

from PySide2.QtCore import QStringListModel, Slot, QModelIndex, Qt, \
    QSortFilterProxyModel, QConcatenateTablesProxyModel
from PySide2.QtWidgets import QWidget, QListView, QPushButton, QTableView, QHBoxLayout, QVBoxLayout, \
    QLineEdit, QFormLayout

from data_preprocessor.data.types import Types
from data_preprocessor.gui import AbsOperationEditor
from data_preprocessor.gui.mainmodels import SearchableAttributeTableWidget, AttributeTableModel, \
    FrameModel
from data_preprocessor.gui.workbench import WorkbenchModel, WorkbenchView
from data_preprocessor.operation.interface.exceptions import OptionValidationError
from data_preprocessor.operation.interface.operation import Operation


class ExtractTimeSeries(Operation):
    def __init__(self, w: WorkbenchModel):
        super().__init__(w)
        self.__series: Dict[str, List[Tuple[str, int]]] = None
        self.__outputName: str = None

    def execute(self) -> Any:
        for series, params in self.__series.items():
            pass

    def setOptions(self, series: Dict[str, List[Tuple[str, int]]], outName: str) -> None:
        # series = { series_name: [ (frameIndex, attributeIndex), ... ] }
        # outName = new workbench entry name
        errors = list()
        if outName in self.workbench.names:
            errors.append(('duplicatename', 'Error: name {} is already present in workbench'.format(
                outName)))
        if not series:
            errors.append(('nooptions', 'Error: no series were added'))
            raise OptionValidationError(errors)
        if not all(series.values()):
            errors.append(('emptyseries', 'Error: some series are empty'))
            raise OptionValidationError(errors)
        self.__series = series
        self.__outputName = outName

    def getEditor(self) -> AbsOperationEditor:
        pass


class _Editor(AbsOperationEditor):
    def editorBody(self) -> QWidget:
        self.body = _ExtractSeriesWidget(self)
        self.body.setWorkbench(self.workbench)
        return self.body

    def getOptions(self) -> Iterable:
        options = dict()
        for si, opts in self.body.series.items():
            index = self.body.seriesListModel.index(si)
            seriesName: str = index.data(Qt.DisplayRole)
            points = list()
            for r in range(self.body.checkedAttributesModel.rowCount()):
                rowIndex: QModelIndex = self.body.checkedAttributesModel.index(r, 0)
                sourceIndex: QModelIndex = self.body.checkedAttributesModel.mapToSource(rowIndex)
                proxy: ProxyIndexModel = sourceIndex.model()
                name: str = proxy.sourceModel().frameModel().name
                attrIndex: int = proxy.mapToSource(sourceIndex).row()
                points.append((name, attrIndex))
            options[seriesName] = points
        outName: str = self.body.entryName.text().strip()
        return options, outName

    def setOptions(self, *args, **kwargs) -> None:
        pass


class _ExtractSeriesWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # { series_index: { dataframe_index: (attribute_index_in_frame, position) } }
        self.series: Dict[int, Dict[int, List[Tuple[int, int]]]] = dict()

        self.addButton = QPushButton('Add series', self)
        self.removeButton = QPushButton('Remove series', self)
        self.seriesListModel = QStringListModel(self)
        self.seriesListView = QListView(self)
        # self.seriesListView.setModel(self.seriesListModel)
        self.seriesListView.setSelectionMode(QListView.SingleSelection)
        self.seriesListModel.rowsInserted.connect(self.editSeries)
        self.addButton.clicked.connect(self.addSeries)
        self.removeButton.clicked.connect(self.removeSeries)

        self.workbenchView = WorkbenchView(self)
        self.attributeTable = SearchableAttributeTableWidget(parent, True, False, False, [Types.Numeric])
        self.workbenchView.selectedRowChanged.connect(self.onFrameSelectionChanged)

        self.checkedAttributesModel = QConcatenateTablesProxyModel(self)
        self.checkedAttributesView = QTableView(self)
        self.entryName = QLineEdit(self)

        layout1 = QVBoxLayout()
        layout1.addWidget(self.addButton)
        layout1.addWidget(self.removeButton)
        layout2 = QHBoxLayout()
        layout2.setSpacing(0)
        layout2.addWidget(self.seriesListView)
        layout2.addLayout(layout1)
        layout2.addSpacing(40)
        layout2.addWidget(self.workbenchView)
        layout2.addWidget(self.attributeTable)
        layout2.addSpacing(40)
        layout2.addWidget(self.checkedAttributesView)
        layout3 = QFormLayout()
        layout3.addRow('Variable name:', self.entryName)
        layout = QVBoxLayout()
        layout.addLayout(layout2)
        layout.addLayout(layout3)
        self.setLayout(layout)

    def setWorkbench(self, w: WorkbenchModel) -> None:
        self.seriesListView.setModel(self.seriesListModel)
        self.workbenchView.setModel(w)
        models = map(lambda mod: CustomAttributeModel(mod, self.checkedAttributesModel), w.modelList)
        proxies: Iterable[ProxyIndexModel] \
            = map(lambda mod: ProxyIndexModel(mod, self.checkedAttributesModel), models)
        for p in proxies:
            self.checkedAttributesModel.addSourceModel(p)
        self.checkedAttributesView.setModel(self.checkedAttributesModel)

    @Slot()
    def removeSeries(self) -> None:
        selected: int = self.seriesListView.currentIndex()
        if selected > 0:
            self.seriesListModel.removeRow(selected)

    @Slot()
    def addSeries(self) -> None:
        newRow = self.seriesListModel.rowCount()
        self.seriesListModel.insertRow(newRow)

    @Slot(QModelIndex, int, int)
    def editSeries(self, index: QModelIndex) -> None:
        self.seriesListView.setCurrentIndex(index)
        self.seriesListView.edit(index)

    @Slot(int)
    def onFrameSelectionChanged(self, frameIndex: int) -> None:
        if frameIndex == -1:
            return
        frameModel = self.workbench.getDataframeModelByIndex(frameIndex)
        self.attributeTable.setSourceFrameModel(frameModel)
        # seriesAttributes: Dict[int, List[Tuple[int, int]]] = self.series.get(
        #     self.seriesListView.currentIndex(), None)
        # checkedAttributes: List[Tuple[int, int]] = seriesAttributes.get(frameIndex, None)
        # checkedAttributes: List[int] = list(map(lambda x: x[0], checkedAttributes))
        # self.attributeTable.model().setChecked(checkedAttributes, True)


class CustomAttributeModel(AttributeTableModel):
    def __init__(self, source: FrameModel, parent=None):
        super().__init__(parent)
        self.attributes: Dict[int, str] = dict()
        self.setFrameModel(source)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 2

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            if index.column() == 0:
                attributeName: str = super().data(index, Qt.DisplayRole)
                frameName: str = self.frameModel().name
                return frameName + '.' + attributeName
            elif index.column() == 1:
                return self.attributes.get(index.row(), None)
        elif role == Qt.EditRole:
            if index.column() == 1:
                return self.attributes.get(index.row(), None)
        return None

    def setData(self, index: QModelIndex, value: str, role: int = Qt.EditRole) -> bool:
        if not index.isValid():
            return False
        if role == Qt.EditRole and index.column() == 1:
            value = value.strip()
            if value and value != index.data(Qt.DisplayRole):
                self.attributes[index.row()] = value
                self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
                return True
        return False


class ProxyIndexModel(QSortFilterProxyModel):
    def __init__(self, source: AttributeTableModel, parent=None):
        super().__init__(parent)
        self.setSourceModel(source)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        index = self.sourceModel().index(source_row, self.sourceModel().checkboxColumn, QModelIndex())
        if index.isValid() and index.data(Qt.DisplayRole) is True:
            return True
        return False
