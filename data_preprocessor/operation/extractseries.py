from typing import Any, Dict, List, Tuple, Iterable, Optional

import pandas as pd
from PySide2.QtCore import Slot, QModelIndex, Qt, \
    QSortFilterProxyModel, QConcatenateTablesProxyModel, QStringListModel, QAbstractItemModel, QLocale, \
    QPersistentModelIndex, Signal, QMimeData
from PySide2.QtGui import QDragEnterEvent
from PySide2.QtWidgets import QWidget, QTableView, QHBoxLayout, QVBoxLayout, \
    QLineEdit, QFormLayout, QHeaderView, QPushButton, QStyledItemDelegate, QComboBox, QGroupBox, \
    QMessageBox

from data_preprocessor import data, exceptions as exp
from data_preprocessor.data.types import Types
from data_preprocessor.gui.editor import AbsOperationEditor
from data_preprocessor.gui.mainmodels import SearchableAttributeTableWidget, AttributeTableModel, \
    SignalTableView
from data_preprocessor.gui.widgetutils import MessageLabel
from data_preprocessor.gui.workbench import WorkbenchModel, WorkbenchView
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

    def shortDescription(self) -> str:
        return 'Allows to extract a temporal information from dataset in non standard format. A ' \
               'standard dataset should have the temporal labels in a single column. If the dataset ' \
               'contains multiple measurements for every time point, these should be uniquely ' \
               'identified using a the time point and an ID, which should be set. This operation ' \
               'assumes that the temporal information is codified over different columns.'

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
            # Additionally sort indexes, otherwise concatenation drops index type
            seriesColumn = seriesColumn.reindex(multiIndex).sort_index(axis=0, ignore_index=False)
            allSeriesColumn.append(seriesColumn)

        # Concat all series in the same dataframe. Remove the 'time' column from index,
        # leaving only the original index (subject id)
        result = pd.concat(allSeriesColumn, axis=1, join='outer', ignore_index=False).reset_index(
            level='time', drop=False)

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
        if not outName:
            errors.append(('noname', 'Error: an output name must be set'))
        if not time:
            errors.append(('notimelabels', 'Error: the time labels are not set'))
        if not series:
            errors.append(('noseries', 'Error: no series are defined'))
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
            raise exp.OptionValidationError(errors)
        self.__series = series
        self.__outputName = outName
        self.__timeLabels = time

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
        seriesOptions: Dict[str, List[Tuple[str, int, int]]] = dict()
        for seriesName, valueDict in self.body.seriesOptions.items():
            seriesOptions[seriesName] = \
                [(frameName, row[0], row[1].row())
                 for frameName, valueList in valueDict.items() for row in valueList]

        outName: str = self.body.outputName.text().strip()
        timeLabels: List[str] = self.body.timeAxisModel.stringList()
        return seriesOptions, timeLabels, outName

    def onAccept(self) -> None:
        # Save selected series option
        selected: List[QModelIndex] = self.body.seriesView.selectedIndexes()
        if selected:
            selectedSeries: str = selected[0].data(Qt.DisplayRole)
            self.body.persistOptionsSetForSeries(selectedSeries)


class _ExtractSeriesWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # {series name: {frame name: [ (Attribute, QPersistentModelIndex) ]
        self.seriesOptions: Dict[str, Dict[str, List[Tuple[int, QPersistentModelIndex]]]] = dict()
        # {frame name: attribute model}
        self.models: Dict[str, CustomProxyAttributeModel] = dict()
        self.seriesView = CustomSignalView(parent=self)
        self.seriesModel = CustomStringListModel(self)
        self.seriesModel.setHeaderLabel('Series name')
        self.addSeriesButton = QPushButton('Add', self)
        self.removeSeriesButton = QPushButton('Remove', self)
        self.addSeriesButton.clicked.connect(self.addSeries)
        self.removeSeriesButton.clicked.connect(self.removeSeries)
        self.seriesView.setModel(self.seriesModel)
        self.seriesView.setDragDropMode(QTableView.InternalMove)
        self.seriesView.setDragDropOverwriteMode(False)
        self.seriesView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.seriesView.verticalHeader().hide()

        # Connect selection to change
        self.seriesView.selectedRowChanged[str, str].connect(self.onSeriesSelectionChanged)
        # When a series is added it should be immediately edited
        self.seriesModel.rowAppended.connect(self.editSeriesName)
        self.seriesModel.rowsInserted.connect(self.checkNoSeries)
        self.seriesModel.rowsRemoved.connect(self.checkNoSeries)

        self.workbenchView = WorkbenchView(self, editable=False)
        self.workbench: WorkbenchModel = None
        self.workbenchView.selectedRowChanged[str, str].connect(self.onFrameSelectionChanged)

        self.attributesView = SearchableAttributeTableWidget(self, True, False, False,
                                                             [Types.Numeric, Types.Ordinal])

        firstRowLayout = QHBoxLayout()
        firstRowLayout.setSpacing(5)

        selectionGroup = QGroupBox(
            title='Select a time series. Then select the columns to add from the current '
                  'datasets', parent=self)
        firstRowLayout.addWidget(self.seriesView)
        buttonLayout = QVBoxLayout()
        buttonLayout.addWidget(self.addSeriesButton)
        buttonLayout.addWidget(self.removeSeriesButton)
        firstRowLayout.addLayout(buttonLayout)
        firstRowLayout.addSpacing(30)
        firstRowLayout.addWidget(self.workbenchView)
        firstRowLayout.addSpacing(30)
        firstRowLayout.addWidget(self.attributesView)
        selectionGroup.setLayout(firstRowLayout)

        # Time axis labels model with add/remove buttons
        self.timeAxisModel = CustomStringListModel(self)
        self.timeAxisModel.setHeaderLabel('Time labels')
        self.timeAxisView = CustomSignalView(self)
        self.timeAxisView.setModel(self.timeAxisModel)
        self.addTimeButton = QPushButton('Add', self)
        self.removeTimeButton = QPushButton('Remove', self)
        self.addTimeButton.clicked.connect(self.addTimeLabel)
        self.removeTimeButton.clicked.connect(self.removeTimeLabel)
        self.timeAxisView.setDragDropMode(QTableView.InternalMove)
        self.timeAxisView.setDragDropOverwriteMode(False)
        self.timeAxisView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.timeAxisView.verticalHeader().hide()
        self.timeAxisModel.rowAppended.connect(self.editTimeLabelName)

        # Concatenation model
        self.timeSeriesDataModel = ConcatenatedModel(self)
        self.timeSeriesDataView = QTableView(self)
        self.timeSeriesDataView.setSelectionMode(QTableView.NoSelection)
        self.timeSeriesDataView.setItemDelegateForColumn(1, ComboBoxDelegate(self.timeAxisModel,
                                                                             self.timeSeriesDataView))
        self.timeSeriesDataView.setEditTriggers(QTableView.CurrentChanged | QTableView.DoubleClicked)
        self.timeSeriesDataView.verticalHeader().hide()
        # Update the label column when some label changes in the label table
        self.timeAxisModel.dataChanged.connect(self.timeSeriesDataModel.timeAxisLabelChanged)

        groupTime = QGroupBox(
            title='Add the time points (ordered) and set the correspondence to every selected column',
            parent=self)
        secondRowLayout = QHBoxLayout()
        secondRowLayout.setSpacing(5)
        # labelLayout = QVBoxLayout()
        # lab = QLabel('Here you should define every time point, in the correct order. After adding '
        #              'double-click a row to edit the point name and drag rows to reorder them', self)
        # lab.setWordWrap(True)
        # labelLayout.addWidget(lab)
        # labelLayout.addWidget(self.timeAxisView)
        secondRowLayout.addWidget(self.timeAxisView)
        timeButtonLayout = QVBoxLayout()
        timeButtonLayout.addWidget(self.addTimeButton)
        timeButtonLayout.addWidget(self.removeTimeButton)
        secondRowLayout.addLayout(timeButtonLayout)
        secondRowLayout.addSpacing(30)
        # labelLayout = QVBoxLayout()
        # lab = QLabel('Every selected column for the current series will be listed here. Click the right '
        #              'column of the table to set the time label associated with every original column',
        #              self)
        # lab.setWordWrap(True)
        # labelLayout.addWidget(lab)
        secondRowLayout.addWidget(self.timeSeriesDataView)
        # secondRowLayout.addLayout(labelLayout)
        groupTime.setLayout(secondRowLayout)

        self.outputName = QLineEdit(self)
        self.warningLabel = MessageLabel(text='', color='orange', icon=QMessageBox.Warning, parent=self)
        lastRowLayout = QFormLayout()
        lastRowLayout.addRow('Output variable name:', self.outputName)
        self.outputName.setPlaceholderText('Output name')
        lastRowLayout.setVerticalSpacing(0)
        lastRowLayout.addRow('', self.warningLabel)
        lastRowLayout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.warningLabel.hide()
        self.outputName.textChanged.connect(self.checkOutputName)

        layout = QVBoxLayout(self)
        layout.addWidget(selectionGroup)
        layout.addWidget(groupTime)
        layout.addLayout(lastRowLayout)
        self.checkNoSeries()

    def setWorkbench(self, w: WorkbenchModel) -> None:
        """ Sets the workbench and initialises every attribute model (one for each frame) """
        self.workbench = w
        self.workbenchView.setModel(w)
        # Set a default name for output
        if self.workbench:
            name = 'time_series_{:d}'
            n = 1
            name_n = name.format(n)
            while name_n in self.workbench.names:
                n += 1
                name_n = name.format(n)
            self.outputName.setText(name_n)

    def addSourceFrameModel(self, frameName: str) -> None:
        if self.workbench:
            dfModel = self.workbench.getDataframeModelByName(frameName)
            # Create an attribute model with checkboxes
            standardModel = AttributeTableModel(self, checkable=True, editable=False, showTypes=True)
            standardModel.setFrameModel(dfModel)
            # Create a proxy to filter data in the concatenation
            customProxy = CustomProxyAttributeModel(self)
            customProxy.setSourceModel(standardModel)
            # Add proxy to the list of models
            self.models[frameName] = customProxy
            # Add proxy as source model
            self.timeSeriesDataModel.addSourceModel(customProxy)

    @Slot()
    def checkNoSeries(self) -> None:
        if not self.seriesModel.rowCount():
            self.workbenchView.setEnabled(False)
            self.attributesView.setEnabled(False)
            self.timeAxisView.setEnabled(False)
            self.addTimeButton.setEnabled(False)
            self.removeTimeButton.setEnabled(False)
            self.timeSeriesDataView.setEnabled(False)
        else:
            self.workbenchView.setEnabled(True)
            self.attributesView.setEnabled(True)
            self.timeAxisView.setEnabled(True)
            self.addTimeButton.setEnabled(True)
            self.removeTimeButton.setEnabled(True)
            self.timeSeriesDataView.setEnabled(True)

    def persistOptionsSetForSeries(self, seriesName: str) -> None:
        if seriesName:
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
            self.seriesOptions[seriesName] = seriesValues

    @Slot(str, str)
    def onSeriesSelectionChanged(self, new: str, old: str) -> None:
        # Save current set options
        self.persistOptionsSetForSeries(old)
        if new:
            # Get options of new selection
            newOptions: Dict[str, List[Tuple[int, QPersistentModelIndex]]] = \
                self.seriesOptions.get(new, dict())
            for frameName, proxyModel in self.models.items():
                frameOptions = newOptions.get(frameName, None)
                self.setOptionsForFrame(frameName, frameOptions)
                # Update proxy view on the time label columns
                proxyModel.dataChanged.emit(
                    proxyModel.index(0, 1, QModelIndex()),
                    proxyModel.index(proxyModel.rowCount() - 1, 1, QModelIndex()),
                    [Qt.DisplayRole, Qt.EditRole])
        # Every time series change clear frame selection in workbench
        self.workbenchView.clearSelection()

    @Slot(str, str)
    def onFrameSelectionChanged(self, newFrame: str, _: str) -> None:
        if not newFrame:
            # Nothing is selected
            return self.attributesView.setAttributeModel(AttributeTableModel(self))
        # Check if frame is already in the source models
        if newFrame not in self.models.keys():
            # Create a new proxy and add it to source models
            self.addSourceFrameModel(newFrame)
            if len(self.models) == 1:
                # If it is the first model added then set up the view
                self.timeSeriesDataView.setModel(self.timeSeriesDataModel)
                self.timeSeriesDataView.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
                self.timeSeriesDataView.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        # Update the attribute table
        self.attributesView.setAttributeModel(self.models[newFrame].sourceModel())

    def setOptionsForFrame(self, frameName: str,
                           options: Optional[List[Tuple[int, QPersistentModelIndex]]]) -> None:
        customProxyModel = self.models[frameName]
        attributeTableModel = customProxyModel.sourceModel()
        attributeTableModel.setAllChecked(False)
        if options:
            proxySelection: Dict[int, QPersistentModelIndex] = {i: pmi for i, pmi in options}
            customProxyModel.attributes = proxySelection
            attributeTableModel.setChecked(list(proxySelection.keys()), value=True)
        else:
            customProxyModel.attributes = dict()

    @Slot()
    def addSeries(self) -> None:
        # Append new row
        self.seriesModel.appendEmptyRow()
        # In oder to avoid copying previous options
        for frameName, proxyModel in self.models.items():
            self.setOptionsForFrame(frameName, None)

    @Slot()
    def removeSeries(self) -> None:
        selected: List[QModelIndex] = self.seriesView.selectedIndexes()
        if selected:
            seriesName: str = selected[0].data(Qt.DisplayRole)
            # Remove row
            self.seriesModel.removeRow(selected[0].row())
            # Remove options for series if they exists
            self.seriesOptions.pop(seriesName, None)

    @Slot()
    def addTimeLabel(self) -> None:
        self.timeAxisModel.appendEmptyRow()

    @Slot()
    def removeTimeLabel(self) -> None:
        selected: List[QModelIndex] = self.timeAxisView.selectedIndexes()
        if selected:
            self.timeAxisModel.removeRow(selected[0].row())
            # Update model
            self.timeSeriesDataModel.dataChanged.emit(
                self.timeSeriesDataModel.index(0, 1, QModelIndex()),
                self.timeSeriesDataModel.index(self.timeSeriesDataModel.rowCount() - 1, 1,
                                               QModelIndex()),
                [Qt.DisplayRole, Qt.EditRole])

    @Slot()
    def editSeriesName(self) -> None:
        index = self.seriesModel.index(self.seriesModel.rowCount() - 1, 0, QModelIndex())
        self.seriesView.setCurrentIndex(index)
        self.seriesView.edit(index)

    @Slot()
    def editTimeLabelName(self) -> None:
        index = self.timeAxisModel.index(self.timeAxisModel.rowCount() - 1, 0, QModelIndex())
        self.timeAxisView.setCurrentIndex(index)
        self.timeAxisView.edit(index)

    @Slot(str)
    def checkOutputName(self, text: str) -> None:
        if self.workbench and text in self.workbench.names:
            self.warningLabel.setText('Variable {:s} will be overwritten'.format(text))
            self.warningLabel.show()
        else:
            self.warningLabel.hide()


class CustomStringListModel(QStringListModel):
    rowAppended = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__headerLabel: str = None
        self.__dragStart: QModelIndex = None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        base = Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable
        if index.isValid():
            # Allow to move elements, but not overwrite them
            base |= Qt.ItemIsDragEnabled
        else:
            base |= Qt.ItemIsDropEnabled
        return base

    def appendEmptyRow(self) -> bool:
        done = self.insertRow(self.rowCount())
        if done:
            self.rowAppended.emit()
        return done

    def setData(self, index: QModelIndex, value: str, role: int = Qt.EditRole) -> bool:
        if index.isValid() and role == Qt.EditRole:
            # If the new value is invalid, then remove the row and quit
            value = value.strip()
            if not value or value in self.stringList():
                self.removeRow(index.row(), index.parent())
                return False
        # In every other case call superclass
        return super().setData(index, value, role)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.__headerLabel
        return None

    def setHeaderLabel(self, lab: str) -> None:
        self.__headerLabel = lab

    def setDragStart(self, index: QModelIndex) -> None:
        # Used by the view to tell where the drag event started
        self.__dragStart = index

    def dropMimeData(self, mData: QMimeData, action: Qt.DropAction, row: int, column: int,
                     parent: QModelIndex) -> bool:
        """ Reimplemented to use moveRow instead of default insertion and removal """
        if action == Qt.MoveAction:
            if row == -1:
                # Then append at the end
                row = self.rowCount() - 1
            self.moveRow(QModelIndex(), self.__dragStart.row(), parent, row)
            self.__dragStart = None
            return False
        return super().dropMimeData(mData, action, row, column, parent)


class CustomSignalView(SignalTableView):
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """ Reimplmented to tell the model the item which is dragged """
        if self.model():
            index = self.indexAt(event.pos())
            self.model().setDragStart(index)
        super().dragEnterEvent(event)


class CustomProxyAttributeModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        # { attributeIndex in source: timeLabelIndex in model }
        self.attributes: Dict[int, QPersistentModelIndex] = dict()

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
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
                return self.attributes.get(sourceIndex.row(), QPersistentModelIndex())
        return super().data(index, role)

    def setData(self, index: QModelIndex, value: QPersistentModelIndex, role: int = Qt.EditRole) -> bool:
        if index.isValid() and role == Qt.EditRole and index.column() == 1:
            sourceIndex = self.mapToSource(index)
            currValue: QPersistentModelIndex = self.attributes.get(sourceIndex.row(), None)
            if value.isValid() and value != currValue:
                self.attributes[sourceIndex.row()] = value
                self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
                return True
        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        base = Qt.ItemIsEnabled | Qt.ItemNeverHasChildren
        if index.isValid() and index.column() == 1:
            base |= Qt.ItemIsEditable
        return base

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        # Show only checked attributes
        index = self.sourceModel().index(source_row, self.sourceModel().checkboxColumn, source_parent)
        return index.isValid() and index.data(Qt.DisplayRole) is True


class ConcatenatedModel(QConcatenateTablesProxyModel):
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
