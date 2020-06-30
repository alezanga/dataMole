from typing import Any, Dict, List, Tuple, Iterable

import pandas as pd
from PySide2.QtCore import Slot, QModelIndex, Qt, \
    QSortFilterProxyModel, QConcatenateTablesProxyModel, QStringListModel, QAbstractItemModel, QLocale, \
    QPersistentModelIndex
from PySide2.QtWidgets import QWidget, QTableView, QHBoxLayout, QVBoxLayout, \
    QLineEdit, QFormLayout, QHeaderView, QPushButton, QStyledItemDelegate, QComboBox

from data_preprocessor import data
from data_preprocessor.data.types import Types
from data_preprocessor.gui import AbsOperationEditor
from data_preprocessor.gui.mainmodels import SearchableAttributeTableWidget, AttributeTableModel, \
    SignalTableView
from data_preprocessor.gui.workbench import WorkbenchModel, WorkbenchView
from data_preprocessor.operation.interface.exceptions import OptionValidationError
from data_preprocessor.operation.interface.operation import Operation


class ExtractTimeSeries(Operation):
    def __init__(self, w: WorkbenchModel):
        super().__init__(w)
        self.__timeLabels: List[str] = list()
        # series_name: (frameName, attrIndex, timeLabelIndex)
        self.__series: Dict[str, List[Tuple[str, int, int]]] = dict()
        self.__outputName: str = None

    @staticmethod
    def name() -> str:
        return 'Extract time series'

    def execute(self) -> None:
        def manipulateDf(s: pd.Series, lab: str, sName: str) -> pd.DataFrame:
            # Makes a dataframe with a value column named as the series and a time label column
            return s.to_frame(sName).assign(time=lab)

        allSeriesColumn: List[pd.DataFrame] = list()
        for seriesName, values in self.__series.items():
            values: List[Tuple[str, int, int]]  # [ (frameName, attrIndex, timeLabelIndex) ]

            # List of frames to append
            frames: List[pd.DataFrame] = list(map(
                lambda tup: manipulateDf(self.workbench.getDataframeModelByName(
                    tup[0]).frame.getRawFrame().iloc[:, tup[1]], self.__timeLabels[tup[2]], seriesName),
                values))

            # Create a dataframe with two columns, one with the values of this series for every index
            # and 1 with the time label. A series column is index by Time and Index. In this way the
            # concatenation of all the series will be made correctly
            seriesColumn = pd.concat(frames, axis=0, join='outer')

            # Create a categorical ordinal index for time labels
            waves = pd.Index(seriesColumn['time'].unique(), name='time',
                             dtype=pd.CategoricalDtype(ordered=True, categories=self.__timeLabels))
            ids = seriesColumn.index.unique()

            # Set index to [id, time]
            seriesColumn = seriesColumn.set_index(['time'], drop=True, append=True)
            # Reindex to provide vales for every possible combination of [time, values]
            multiIndex: pd.MultiIndex = pd.MultiIndex.from_product([ids, waves])
            seriesColumn = seriesColumn.reindex(multiIndex)
            allSeriesColumn.append(seriesColumn)

        # Concat all series in the same dataframe. Remove the 'time' column from index,
        # leaving only the original index (subject id)
        result = pd.concat(allSeriesColumn, axis=1, join='outer').reset_index(level='time', drop=False)

        # Result:
        # Index is set on the subject identifier
        # Column 'time' contains the names of the time axis (wave names or integers)
        # The other columns are named with the specified 'seriesName' and are the series values which
        # varies with time and index
        self._workbench.setDataframeByName(self.__outputName, data.Frame(result))

    def needsOptions(self) -> bool:
        return True

    def setOptions(self, series: Dict[str, List[Tuple[str, int, int]]], time: List[str],
                   outName: str) -> None:
        # series = { series: [ (frameName, attributeIndex, timeLabelIndex) ] }
        # outName = new workbench entry name
        # time = [ 'wave1', 'wave2', ... ]
        errors = list()
        if outName in self.workbench.names:
            errors.append(('duplicatename', 'Error: name {} is already present in workbench'.format(
                outName)))
        if not time:
            errors.append(('notimelabels', 'Error: the time labels are not set'.format(outName)))
        if not series:
            errors.append(('nooptions', 'Error: series is empty'))
        else:
            lengthOk = all(map(lambda s: s and len(s) == len(time), series.values()))
            noDuplicates = all(map(lambda s: s and len(set(map(lambda t: t[2], s))) == len(s),
                                   series.values()))
            if not lengthOk:
                errors.append(('length', 'Error: you set {:d} time labels, but some series is made up '
                                         'of a different number of attributes'.format(len(time))))
            if not noDuplicates:
                errors.append(('duplicates', 'Error: some series contain duplicated time labels'))
        if errors:
            raise OptionValidationError(errors)
        self.__series = series
        self.__outputName = outName
        self.__timeLabels = time

    def getOptions(self) -> Iterable:
        return tuple()  # Does not matter for this operation

    def getEditor(self) -> AbsOperationEditor:
        return _ExtractSeriesEditor()

    def injectEditor(self, editor: 'AbsOperationEditor') -> None:
        editor.workbench = self.workbench
        editor.refresh()


export = ExtractTimeSeries


class _ExtractSeriesEditor(AbsOperationEditor):
    def editorBody(self) -> QWidget:
        self.body = _ExtractSeriesWidget(self)
        return self.body

    def refresh(self) -> None:
        self.body.setWorkbench(self.workbench)

    def getOptions(self) -> Iterable:
        self.body.seriesView.clearSelection()

        seriesOptions: Dict[str, List[Tuple[str, int, int]]] = dict()
        for seriesIndex, valueDict in self.body.seriesOptions.items():
            seriesName: str = self.body.seriesModel.index(seriesIndex).data(Qt.DisplayRole)
            seriesOptions[seriesName] = \
                [(frameName, row[0], row[1].row())
                 for frameName, valueList in valueDict.items() for row in valueList]

        outName: str = self.body.outputName.text().strip()
        timeLabels: List[str] = self.body.timeAxisModel.stringList()
        return seriesOptions, timeLabels, outName

    def setOptions(*args, **kwargs) -> None:
        pass


class _ExtractSeriesWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # {series index: {frame name: [ (Attribute, QPersistentModelIndex) ]
        self.seriesOptions: Dict[int, Dict[str, List[Tuple[int, QPersistentModelIndex]]]] = dict()
        self.models: Dict[int, CustomProxyAttributeModel] = dict()
        self.seriesView = SignalTableView(parent=self)
        self.seriesModel = CustomStringListModel(self)
        self.seriesModel.setHeaderLabel('Series name')
        self.addSeriesButton = QPushButton('Add', self)
        self.removeSeriesButton = QPushButton('Remove', self)
        self.addSeriesButton.clicked.connect(self.addSeries)
        self.removeSeriesButton.clicked.connect(self.removeSeries)
        self.seriesView.setDragDropMode(QTableView.InternalMove)
        self.seriesView.setDragDropOverwriteMode(False)
        self.seriesView.setModel(self.seriesModel)
        self.seriesView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.seriesView.verticalHeader().hide()

        # Connect selection to change
        self.seriesView.selectedRowChanged.connect(self.onSeriesSelectionChanged)
        # When a series is added it should be immediately edited
        self.seriesModel.rowsInserted.connect(self.editSeriesName)

        self.workbenchView = WorkbenchView(self)
        self.workbench: WorkbenchModel = None
        self.attributesView = SearchableAttributeTableWidget(parent, True, False, False,
                                                             [Types.Numeric, Types.Ordinal])
        self.workbenchView.selectedRowChanged.connect(self.onFrameSelectionChanged)

        firstRowLayout = QHBoxLayout()
        firstRowLayout.addWidget(self.seriesView)
        buttonLayout = QVBoxLayout()
        buttonLayout.addWidget(self.addSeriesButton)
        buttonLayout.addWidget(self.removeSeriesButton)
        firstRowLayout.addLayout(buttonLayout)
        firstRowLayout.addWidget(self.workbenchView)
        firstRowLayout.addWidget(self.attributesView)

        # Time axis labels model with add/remove buttons
        self.timeAxisModel = CustomStringListModel(self)
        self.timeAxisModel.setHeaderLabel('Time labels')
        self.timeAxisView = SignalTableView(self)
        self.addTimeButton = QPushButton('Add', self)
        self.removeTimeButton = QPushButton('Remove', self)
        self.addTimeButton.clicked.connect(self.addTimeLabel)
        self.removeTimeButton.clicked.connect(self.removeTimeLabel)
        self.timeAxisView.setDragDropMode(QTableView.InternalMove)
        self.timeAxisView.setDragDropOverwriteMode(False)
        self.timeAxisView.setModel(self.timeAxisModel)
        self.timeAxisView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.timeAxisView.verticalHeader().hide()
        self.timeAxisModel.rowsInserted.connect(self.editTimeLabelName)

        # Concatenation model
        self.timeSeriesDataModel = ConcatenatedModel(self)
        self.timeSeriesDataView = SignalTableView(self)
        self.timeSeriesDataView.setSelectionMode(QTableView.NoSelection)
        self.timeSeriesDataView.setItemDelegateForColumn(1, ComboBoxDelegate(self.timeAxisModel,
                                                                             self.timeSeriesDataView))
        self.timeSeriesDataView.verticalHeader().hide()
        # Update the label column when some label changes in the label table
        self.timeAxisModel.dataChanged.connect(self.timeSeriesDataModel.timeAxisLabelChanged)

        secondRowLayout = QHBoxLayout()
        secondRowLayout.setSpacing(5)
        secondRowLayout.addWidget(self.timeAxisView)
        timeButtonLayout = QVBoxLayout()
        timeButtonLayout.addWidget(self.addTimeButton)
        timeButtonLayout.addWidget(self.removeTimeButton)
        secondRowLayout.addLayout(timeButtonLayout)
        secondRowLayout.addSpacing(35)
        secondRowLayout.addWidget(self.timeSeriesDataView)

        self.outputName = QLineEdit(self)
        lastRowLayout = QFormLayout()
        lastRowLayout.addRow('Output variable name:', self.outputName)

        layout = QVBoxLayout(self)
        layout.addLayout(firstRowLayout)
        layout.addLayout(secondRowLayout)
        layout.addLayout(lastRowLayout)

    def setWorkbench(self, w: WorkbenchModel) -> None:
        self.workbench = w
        self.workbenchView.setModel(w)

    def persistOptionsSetForSeries(self, seriesIndex: int) -> None:
        if seriesIndex is not None and seriesIndex >= 0:
            seriesValues: Dict[str, List[Tuple[int, QPersistentModelIndex]]] = dict()
            for r in range(self.timeSeriesDataModel.rowCount()):
                column0Index: QModelIndex = self.timeSeriesDataModel.index(r, 0, QModelIndex())
                column1Index: QModelIndex = self.timeSeriesDataModel.index(r, 1, QModelIndex())
                sourceIndex: QModelIndex = self.timeSeriesDataModel.mapToSource(column0Index)
                proxy: CustomProxyAttributeModel = sourceIndex.model()
                frameName: str = proxy.sourceModel().frameModel().name
                attrIndexInFrame: int = proxy.mapToSource(sourceIndex).row()
                timeLabelIndex: QPersistentModelIndex = column1Index.data(Qt.DisplayRole)
                if seriesValues.get(frameName, None):
                    seriesValues[frameName].append((attrIndexInFrame, timeLabelIndex))
                else:
                    seriesValues[frameName] = [(attrIndexInFrame, timeLabelIndex)]
            self.seriesOptions[seriesIndex] = seriesValues

    @Slot(QModelIndex, int, int)
    def editSeriesName(self, parent: QModelIndex, first: int, _: int) -> None:
        index = self.seriesModel.index(first, 0, parent)
        self.seriesView.setCurrentIndex(index)
        self.seriesView.edit(index)

    @Slot(QModelIndex, int, int)
    def editTimeLabelName(self, parent: QModelIndex, first: int, _: int) -> None:
        index = self.timeAxisModel.index(first, 0, parent)
        self.timeAxisView.setCurrentIndex(index)
        self.timeAxisView.edit(index)

    @Slot(int, int)
    def onSeriesSelectionChanged(self, new: int, old: int) -> None:
        clearViews: bool = False
        # Save current set options
        self.persistOptionsSetForSeries(old)
        if new >= 0:
            # Get options of new selection
            newOptions: Dict[str, List[Tuple[int, QPersistentModelIndex]]] = \
                self.seriesOptions.get(new, None)
            if newOptions:
                for frameIndex, proxyModel in self.models.items():
                    frameName: str = self.workbench.getDataframeModelByIndex(frameIndex).name
                    attributeModel: AttributeTableModel = proxyModel.sourceModel()
                    frameOptions = newOptions.get(frameName, None)
                    # Reset checked attributes
                    if frameOptions:
                        attributeModel.setAllChecked(False)
                        proxySelection: Dict[int, QPersistentModelIndex] = {i: pmi for i, pmi in
                                                                            frameOptions}
                        proxyModel.attributes = proxySelection
                        attributeModel.setChecked(list(proxySelection.keys()), value=True)
                    else:
                        clearViews = True
            else:
                clearViews = True
        if clearViews:
            for proxyModel in self.models.values():
                attributeModel: AttributeTableModel = proxyModel.sourceModel()
                attributeModel.setAllChecked(False)
                proxyModel.attributes = dict()
                # Update proxy view
                proxyModel.dataChanged.emit(
                    proxyModel.index(0, 1, QModelIndex()),
                    proxyModel.index(proxyModel.rowCount() - 1, 1, QModelIndex()),
                    [Qt.DisplayRole, Qt.EditRole])

    @Slot(int)
    def onFrameSelectionChanged(self, frameIndex: int) -> None:
        if frameIndex == -1:
            return
        customModel = self.models.get(frameIndex, None)
        # Get the frame model
        frameModel = self.workbench.getDataframeModelByIndex(frameIndex)
        if customModel:
            self.attributesView.setAttributeModel(customModel.sourceModel())
        else:
            # Create an attribute model with checkboxes
            standardModel = AttributeTableModel(None, checkable=True, editable=False, showTypes=True)
            standardModel.setFrameModel(frameModel)
            # Create a custom proxy model which hides checkboxes, filters and shows custom info
            customModel = CustomProxyAttributeModel(self)
            customModel.setSourceModel(standardModel)
            standardModel.setParent(customModel)
            # Save custom model for reuse and set it in the table
            self.models[frameIndex] = customModel
            self.attributesView.setAttributeModel(standardModel)
            # Add to concatenation in big proxy model
            self.timeSeriesDataModel.addSourceModel(customModel)
            if not self.timeSeriesDataView.model():
                self.timeSeriesDataView.setModel(self.timeSeriesDataModel)
            self.timeSeriesDataView.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.timeSeriesDataView.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

    @Slot()
    def addSeries(self) -> None:
        self.seriesModel.insertRow(self.seriesModel.rowCount())

    @Slot()
    def removeSeries(self) -> None:
        self.seriesModel.removeRow(self.seriesView.selectedIndexes()[0].row())

    @Slot()
    def addTimeLabel(self) -> None:
        self.timeAxisModel.insertRow(self.timeAxisModel.rowCount())

    @Slot()
    def removeTimeLabel(self) -> None:
        self.timeAxisModel.removeRow(self.timeAxisModel.selectedIndexes()[0].row())


class CustomStringListModel(QStringListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.__label = None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        base = Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled
        if not index.isValid():
            # Allow to move elements, but not overwrite them
            base |= Qt.ItemIsDropEnabled
        return base

    def setData(self, index: QModelIndex, value: str, role: int = Qt.EditRole) -> bool:
        if index.isValid() and role == Qt.EditRole:
            # If the new value is invalid, then remove the row and quit
            value = value.strip()
            if not value:
                self.removeRow(index.row(), index.parent())
                return False
        # In every other case call superclass
        return super().setData(index, value, role)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.__label
        return None

    def setHeaderLabel(self, lab: str) -> None:
        self.__label = lab


class CustomProxyAttributeModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        # { attributeIndex in source: timeLabelIndex in model }
        self.attributes: Dict[int, QPersistentModelIndex] = dict()

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 2

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if index.isValid():
            sourceIndex = self.mapToSource(index)
            if role == Qt.DisplayRole and index.column() == 0:
                dataIndex = self.sourceModel().index(sourceIndex.row(),
                                                     self.sourceModel().nameColumn,
                                                     sourceIndex.parent())
                attributeName: str = dataIndex.data(Qt.DisplayRole)
                frameName: str = self.sourceModel().frameModel().name
                return frameName + '.' + attributeName
            elif index.column() == 1 and (role == Qt.EditRole or role == Qt.DisplayRole):
                return self.attributes.get(index.row(), QPersistentModelIndex())
        return super().data(index, role)

    def setData(self, index: QModelIndex, value: QPersistentModelIndex, role: int = Qt.EditRole) -> bool:
        if index.isValid() and role == Qt.EditRole and index.column() == 1:
            currValue: QPersistentModelIndex = self.attributes.get(index.row(), None)
            if value.isValid() and value != currValue:
                self.attributes[index.row()] = value
                self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
                return True
        return False

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        # Show only checked attributes
        index = self.sourceModel().index(source_row, self.sourceModel().checkboxColumn, source_parent)
        return index.isValid() and index.data(Qt.DisplayRole) is True


class ConcatenatedModel(QConcatenateTablesProxyModel):
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        f = Qt.ItemNeverHasChildren | super().flags(index)
        if index.column() == 1:
            f |= Qt.ItemIsEditable
        return f

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == 0:
                return 'Series values'
            elif section == 1:
                return 'Time labels'
        return None

    @Slot(QModelIndex, QModelIndex, list)
    def timeAxisLabelChanged(self, tl, br, roles) -> None:
        if Qt.DisplayRole in roles:
            self.dataChanged.emit(self.index(0, 1, QModelIndex()),
                                  self.index(self.rowCount() - 1, 1, QModelIndex()),
                                  [Qt.DisplayRole])


class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, timeModel: QStringListModel, parent=None):
        super().__init__(parent)
        self.__timeLabelModel: QStringListModel = timeModel

    def createEditor(self, parent: QWidget, option, index: QModelIndex) -> QWidget:
        return QComboBox(parent)

    def setEditorData(self, editor: QComboBox, index: QModelIndex) -> None:
        editor.setModel(self.__timeLabelModel)

    def setModelData(self, editor: QComboBox, model: QAbstractItemModel, index: QModelIndex) -> None:
        selectedIndex: int = editor.currentIndex()
        mi = QPersistentModelIndex()
        if selectedIndex is not None and selectedIndex >= 0:
            mi = QPersistentModelIndex(self.__timeLabelModel.index(selectedIndex))
        model.setData(index, mi, Qt.EditRole)

    def displayText(self, value: QPersistentModelIndex, locale: QLocale) -> str:
        if value and value.isValid():
            return value.data(Qt.DisplayRole)
        return ''
