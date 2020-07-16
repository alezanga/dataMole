import abc
from enum import Enum
from typing import Any, List, Union, Dict, Tuple, Optional, Set

from PySide2 import QtGui
from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal, Slot, QAbstractItemModel, \
    QSortFilterProxyModel, QItemSelection, QThreadPool, QEvent, QRect, QPoint, \
    QRegularExpression, QIdentityProxyModel, QAbstractProxyModel, QMutex
from PySide2.QtGui import QPainter
from PySide2.QtWidgets import QWidget, QTableView, QLineEdit, QVBoxLayout, QHeaderView, QLabel, \
    QHBoxLayout, QStyleOptionViewItem, QStyleOptionButton, QStyle, QApplication, \
    QStyledItemDelegate, QMessageBox

from data_preprocessor import gui, flogging
from data_preprocessor.data import Frame, Shape
from data_preprocessor.data.types import Types, Type, ALL_TYPES
from data_preprocessor.operation.computations.statistics import AttributeStatistics, Hist
from data_preprocessor.threads import Worker


# New role to return raw data from header
class MyRoles(Enum):
    DataRole = Qt.UserRole


class FrameModel(QAbstractTableModel):
    """ Table model for a single dataframe """

    DataRole = MyRoles.DataRole
    statisticsComputed = Signal(tuple)
    statisticsError = Signal(tuple)

    def __init__(self, parent: QWidget = None, frame: Union[Frame, Shape] = Frame()):
        super().__init__(parent)
        if isinstance(frame, Frame):
            self.__frame: Frame = frame
            self.__shape: Shape = self.__frame.shape
        elif isinstance(frame, Shape):  # it's a Shape
            self.__frame: Frame = Frame()
            self.__shape: Shape = frame
        else:
            self.__frame: Frame = Frame()
            self.__shape: Shape = Shape()
        # Dictionary { attributeIndex: value }
        self._statistics: Dict[int, Dict[str, object]] = dict()
        self._histogram: Dict[int, Dict[Any, int]] = dict()
        # Dataframe name
        self.name: str = ''
        # Set of alive workers by identifier (attribute number, type, operation)
        self._runningWorkers: Set[Tuple] = set()
        self._dataAccessMutex = QMutex()

    @property
    def frame(self) -> Frame:
        return self.__frame

    @property
    def shape(self) -> Shape:
        return self.__shape

    def setFrame(self, frame: Frame) -> None:
        self.beginResetModel()
        self.__frame = frame
        self.__shape: Shape = self.__frame.shape
        self._statistics = dict()
        self._histogram = dict()
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return self.frame.nRows  # True number of rows

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return self.shape.nColumns

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self.__frame.getRawFrame().iloc[index.row(), index.column()])
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self.__shape.colNames[section] + '\n' + self.__shape.colTypes[section].name
            elif role == FrameModel.DataRole.value:
                return self.__shape.colNames[section], self.__shape.colTypes[section]
        # Vertical header shows row number
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            return section
        return None

    def setHeaderData(self, section: int, orientation: Qt.Orientation, value: Any, role: int = ...) \
            -> bool:
        """ Change column name """
        if orientation == Qt.Horizontal and role == Qt.EditRole and section < self.columnCount():
            names = self.__frame.colnames
            names[section] = value
            self.__frame = self.__frame.rename({self.headerData(section, orientation,
                                                                FrameModel.DataRole.value)[0]: value})
            self.__shape.colNames[section] = value
            self.headerDataChanged.emit(orientation, section, section)
            return True
        return False

    @property
    def statistics(self) -> Dict[int, Dict[str, object]]:
        return self._statistics

    @property
    def histogram(self) -> Dict[int, Dict[Any, int]]:
        return self._histogram

    def existsRunningTask(self, identifier) -> bool:
        # Check if a task is already running for this attribute
        exists: bool = False
        if identifier in self._runningWorkers:
            exists = True
        return exists

    def computeStatistics(self, attribute: int) -> None:
        """ Compute statistics for a given attribute """
        flogging.appLogger.debug('computeStatistics() called, attribute {:d}'.format(attribute))
        attType = self.__shape.colTypes[attribute]
        identifier = (attribute, attType, 'stat')
        if self.__frame.nRows == 0:
            return self.onWorkerError((attribute, attType, 'stat'), tuple())
        # Check if a task is already running for this attribute
        if self.existsRunningTask(identifier):
            return
        # Create a new task
        stats = AttributeStatistics()
        stats.setOptions(attribute=attribute)
        statWorker = Worker(stats, args=(self.__frame,), identifier=identifier)
        rc = statWorker.signals.result.connect(self.onWorkerSuccess, Qt.DirectConnection)
        ec = statWorker.signals.error.connect(self.onWorkerError, Qt.DirectConnection)
        fc = statWorker.signals.finished.connect(self.onWorkerFinished, Qt.DirectConnection)
        flogging.appLogger.debug('Connected stat worker: {:b}, {:b}, {:b}'.format(rc, ec, fc))
        # Remember which computations are already in progress
        self._runningWorkers.add(identifier)
        QThreadPool.globalInstance().start(statWorker)

    def computeHistogram(self, attribute: int, histBins: int) -> None:
        flogging.appLogger.debug('computeHistogram() called, attribute {:d}'.format(attribute))
        attType = self.__shape.colTypes[attribute]
        identifier = (attribute, attType, 'hist')
        if self.__frame.nRows == 0:
            return self.onWorkerError((attribute, attType, 'hist'), tuple())
        # Check if a task is already running for this attribute
        if self.existsRunningTask(identifier):
            return
        # Create a new task
        hist = Hist()
        hist.setOptions(attribute=attribute, attType=attType, bins=histBins)
        histWorker = Worker(hist, args=(self.__frame,), identifier=identifier)
        rc = histWorker.signals.result.connect(self.onWorkerSuccess, Qt.DirectConnection)
        ec = histWorker.signals.error.connect(self.onWorkerError, Qt.DirectConnection)
        fc = histWorker.signals.finished.connect(self.onWorkerFinished, Qt.DirectConnection)
        flogging.appLogger.debug('Connected hist worker: {:b}, {:b}, {:b}'.format(rc, ec, fc))
        # Remember computations in progress
        self._runningWorkers.add(identifier)
        QThreadPool.globalInstance().start(histWorker)

    @Slot(object, object)
    def onWorkerSuccess(self, identifier: Tuple[int, Type, str], result: Dict[Any, Any]) -> None:
        attribute, attType, mode = identifier
        if mode == 'stat':
            self._dataAccessMutex.lock()
            self._statistics[attribute] = result
            self._dataAccessMutex.unlock()
            flogging.appLogger.debug('Statistics computation succeeded')
        elif mode == 'hist':
            self._dataAccessMutex.lock()
            self._histogram[attribute] = result
            self._dataAccessMutex.unlock()
            flogging.appLogger.debug('Histogram computation succeeded')
        self.statisticsComputed.emit(identifier)

    @Slot(object, tuple)
    def onWorkerError(self, identifier: Tuple[int, Type, str],
                      error: Tuple[type, Exception, str]) -> None:
        if error:
            flogging.appLogger.error('Statistics computation (mode "{}") failed with {}: {}\n{}'.format(
                identifier[2], *error))
        self.statisticsError.emit(identifier)

    @Slot(object)
    def onWorkerFinished(self, identifier: Tuple[int, Type, str]) -> None:
        flogging.appLogger.debug('Worker (mode "{}") finished'.format(identifier[2]))
        self._runningWorkers.remove(identifier)

    # def checkWorkerFinished(self, identifier: Tuple[int, Type, str]) -> None:
    #     """ Delete worker with specified identifier from worker dictionary if the worker
    #     completed by receiving a result/error and a 'finished' signal. Otherwise keep track of the
    #     status in order to delete it at the proper moment. This is necessary because the reception
    #     order of signals across threads is unspecified """
    #     w: Tuple[Worker, bool] = self._workers[identifier]
    #     print(identifier[0], w[1])
    #     if w[1] is True:
    #         # Worker can be deleted
    #         o = self._workers.pop(identifier)
    #         shiboken2.delete(o[0])
    #     else:
    #         # Set flag to delete worker at next call
    #         self._workers[identifier] = (w[0], True)


class IncrementalRenderFrameModel(QIdentityProxyModel):
    DEFAULT_COL_BATCH_SIZE = 300
    DEFAULT_ROW_BATCH_SIZE = 400

    def __init__(self, rowBatch: int = DEFAULT_ROW_BATCH_SIZE,
                 colBatch: int = DEFAULT_COL_BATCH_SIZE, parent: QWidget = None):
        super().__init__(parent)
        self._batchRows: int = rowBatch
        self._batchCols: int = colBatch
        self._loadedCols: int = self._batchCols
        self._loadedRows: int = self._batchRows
        self._scrollMode: str = None  # {'row', 'column'}

    def setScrollMode(self, mode: str) -> None:
        self._scrollMode = mode

    def setBatchRowSize(self, size: int) -> None:
        self._batchRows = size

    def setBatchColSize(self, size: int) -> None:
        self._batchCols = size

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid() or not self.sourceModel():
            return 0
        return min(self._loadedRows, self.sourceModel().rowCount())

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid() or not self.sourceModel():
            return 0
        return min(self._loadedCols, self.sourceModel().columnCount())

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if not self.sourceModel():
            return None
        if orientation == Qt.Vertical:
            indexes: List = self.sourceModel().frame.indexValues
            indexLen: int = self.sourceModel().shape.nIndexLevels
            if role == Qt.DisplayRole:
                if indexLen == 1:
                    return str(indexes[section])
                else:
                    return '  '.join([str(i) for i in indexes[section]])
        return super().headerData(section, orientation, role)

    def canFetchMore(self, parent: QModelIndex) -> bool:
        """ Returns True if more columns should be displayed, False otherwise """
        if not self.sourceModel():
            return False
        return self._loadedCols < self.sourceModel().columnCount() if self._scrollMode == 'column' \
            else self._loadedRows < self.sourceModel().rowCount()

    def fetchMore(self, parent: QModelIndex):
        if self._scrollMode == 'column':
            remainder = self.sourceModel().columnCount() - self._loadedCols
            colsToFetch = min(remainder, self._batchCols)
            self.beginInsertColumns(parent, self._loadedCols, self._loadedCols + colsToFetch - 1)
            self._loadedCols += colsToFetch
            self.endInsertColumns()
        elif self._scrollMode == 'row':
            remainder = self.sourceModel().rowCount() - self._loadedRows
            rowsToFetch = min(remainder, self._batchRows)
            self.beginInsertRows(parent, self._loadedRows, self._loadedRows + rowsToFetch - 1)
            self._loadedRows += rowsToFetch
            self.endInsertRows()


class AbstractAttributeModel(abc.ABC):
    """ Interface for models used to display attributes information """

    @property
    @abc.abstractmethod
    def checkboxColumn(self) -> Optional[int]:
        """
        Return the index of checkbox column in the current model or None if no such column exists
        """
        pass

    @property
    @abc.abstractmethod
    def typeColumn(self) -> Optional[int]:
        """ Return index of the column displaying types in the current model or None if no such column
        exists """
        pass

    @property
    @abc.abstractmethod
    def nameColumn(self) -> Optional[int]:
        """ Return index of the column displaying the attribute name in the current model or None if no
        such column exists """
        pass

    @abc.abstractmethod
    def frameModel(self) -> Optional[FrameModel]:
        """ Return the frame model being displayed in the model, or None if no model is set """
        pass

    @abc.abstractmethod
    def setFrameModel(self, model: FrameModel) -> None:
        """ Set the frame model to display """
        pass

    @property
    @abc.abstractmethod
    def checked(self) -> Optional[List[int]]:
        """ Get selected rows if the model is checkable, otherwise return None """
        pass

    @abc.abstractmethod
    def setChecked(self, rows: List[int], value: bool) -> None:
        """ Set all specified checkboxes to value. Other rows are left untouched """
        pass

    @abc.abstractmethod
    def setAllChecked(self, value: bool) -> None:
        """ Set all rows checked or unchecked """
        pass

    @Slot(int)
    def onHeaderClicked(self, section: int) -> None:
        """ Slot to be called when user clicks on the table header """
        if section == self.checkboxColumn:
            checked = self.headerData(section, Qt.Horizontal, Qt.DisplayRole)
            if checked is True:
                self.setAllChecked(False)
            else:
                self.setAllChecked(True)


class AttributeTableModelMeta(type(AbstractAttributeModel), type(QAbstractTableModel)):
    """ Metaclass for mixin """
    pass


class AttributeProxyModelMeta(type(AbstractAttributeModel), type(QSortFilterProxyModel)):
    """ Metaclass for mixin """
    pass


class AttributeTableModel(AbstractAttributeModel, QAbstractTableModel,
                          metaclass=AttributeTableModelMeta):
    def __init__(self, parent: QWidget = None, checkable: bool = False, editable: bool = False,
                 showTypes: bool = True):
        """ Creates a tablemodel to hold attributes list

        :param parent: parent widget
        :param checkable: whether an additional column with checkbox must be added
        :param editable: whether the model must support attribute renaming
        """
        super().__init__(parent)
        self._checkable: bool = checkable
        self._showTypes: bool = showTypes
        self._editable: bool = editable
        # Keeps track of checked items
        self._checked: List[bool] = list()
        self._frameModel: FrameModel = None

    @property
    def checkboxColumn(self) -> Optional[int]:
        if self._checkable:
            return 0
        else:
            return None

    @property
    def typeColumn(self) -> Optional[int]:
        if self._showTypes:
            if self._checkable:
                return 2
            else:
                return 1
        else:
            return None

    @property
    def nameColumn(self) -> Optional[int]:
        if self._checkable:
            return 1
        else:
            return 0

    def frameModel(self) -> Optional[FrameModel]:
        return self._frameModel

    @property
    def checked(self) -> Optional[List[int]]:
        return [i for i, v in enumerate(self._checked) if v] if self._checkable else None

    def setChecked(self, rows: List[int], value: bool) -> None:
        if not self._checked or not rows:
            return
        for r in rows:
            self._checked[r] = value
        # Reset column from minimum to maximum changed row
        sIndex = self.index(min(rows), self.checkboxColumn, QModelIndex())
        eIndex = self.index(max(rows), self.checkboxColumn, QModelIndex())
        self.dataChanged.emit(sIndex, eIndex, [Qt.DisplayRole, Qt.EditRole])

    def setAllChecked(self, value: bool) -> None:
        if value is True:
            self._checked = [True] * self.rowCount()
        else:
            self._checked = [False] * self.rowCount()
        sIndex = self.index(0, self.checkboxColumn, QModelIndex())
        eIndex = self.index(self.rowCount() - 1, self.checkboxColumn, QModelIndex())
        self.dataChanged.emit(sIndex, eIndex, [Qt.DisplayRole, Qt.EditRole])

    def setFrameModel(self, model: FrameModel) -> None:
        if self._frameModel is model:
            return

        self.beginResetModel()

        # Disconnect this model from old model' signals
        if self._frameModel:
            self._frameModel.disconnect(self)

        # Update checked state
        if self._checkable:
            self._checked = [False] * model.columnCount(QModelIndex())

        self._frameModel = model

        # Connect to new model
        # NOTE: Some of these are NOT slots
        # self._frameModel.modelAboutToBeReset.connect(self.beginResetModel)
        self._frameModel.modelReset.connect(self.onFrameReset)
        self._frameModel.headerDataChanged.connect(self.onHeaderChanged)
        self._frameModel.columnsAboutToBeInserted.connect(self.onColumnsAboutToBeInserted)
        self._frameModel.columnsAboutToBeMoved.connect(self.onColumnsAboutToBeMoved)
        self._frameModel.columnsAboutToBeRemoved.connect(self.onColumnsAboutToBeRemoved)
        self._frameModel.columnsInserted.connect(self.endInsertRows)
        self._frameModel.columnsMoved.connect(self.endMoveRows)
        self._frameModel.columnsRemoved.connect(self.endRemoveRows)

        self.endResetModel()

    @Slot()
    def onFrameReset(self) -> None:
        self.beginResetModel()
        if self._checkable:
            self._checked = [False] * self._frameModel.columnCount(QModelIndex())
        self.endResetModel()

    @Slot(QModelIndex, int, int)
    def onColumnsAboutToBeInserted(self, parent: QModelIndex, first: int, last: int) -> None:
        self.beginInsertRows(parent, first, last)

    @Slot(QModelIndex, int, int, QModelIndex, int)
    def onColumnsAboutToBeMoved(self, sourceParent: QModelIndex, sourceStart: int, sourceEnd: int,
                                destinationParent: QModelIndex, destinationColumns: int) -> None:
        self.beginMoveRows(sourceParent, sourceStart, sourceEnd,
                           destinationParent, destinationColumns)

    @Slot(QModelIndex, int, int)
    def onColumnsAboutToBeRemoved(self, parent: QModelIndex, first: int, last: int) -> None:
        self.beginInsertRows(parent, first, last)

    @Slot(Qt.Orientation, int, int)
    def onHeaderChanged(self, orientation: Qt.Orientation, sec1: int, sec2: int) -> None:
        if orientation == Qt.Horizontal:
            self.dataChanged.emit(self.index(sec1, self.nameColumn),
                                  self.index(sec2, self.nameColumn))

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid() or not self._frameModel:
            return 0
        return self._frameModel.columnCount()

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        if self._checkable ^ self._showTypes:
            return 2
        elif self._checkable:  # Show everything
            return 3
        else:  # Only name
            return 1

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None

        if role == Qt.DisplayRole or role == Qt.EditRole:
            if index.column() == self.checkboxColumn:
                return self._checked[index.row()]
            name: str
            col_type: Type
            name, col_type = self._frameModel.headerData(index.row(), orientation=Qt.Horizontal,
                                                         role=FrameModel.DataRole.value)
            value = None
            if index.column() == self.nameColumn:
                value = name
            elif index.column() == self.typeColumn:
                value = col_type.name
            return value
        elif role == Qt.ToolTipRole and index.column() == self.typeColumn:
            _, col_type = self._frameModel.headerData(index.row(), orientation=Qt.Horizontal,
                                                      role=FrameModel.DataRole.value)
            if col_type is Types.Ordinal:
                sortedCategories = self._frameModel.frame.getRawFrame() \
                                       .iloc[:, index.row()].dtype.categories
                return ' < '.join(sortedCategories)
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        return None

    def setData(self, index: QModelIndex, value: Any, role: int = ...) -> bool:
        # NOTE: does not support changing type for now (only name)
        if not index.isValid():
            return False

        if role == Qt.EditRole:
            # Change attribute name
            if index.column() == self.nameColumn:
                value: str = value.strip()
                if not value or value == index.data(Qt.DisplayRole):
                    return False
                if value in self._frameModel.frame.colnames:
                    gui.notifier.addMessage('Rename error', 'New name "{}" is duplicate'.format(value),
                                            QMessageBox.Critical)
                    return False
                return self._frameModel.setHeaderData(index.row(), Qt.Horizontal, value, Qt.EditRole)
            # Toggle checkbox state
            elif index.column() == self.checkboxColumn:
                i: int = index.row()
                self._checked[i] = value
                self.dataChanged.emit(index, index)
                self.headerDataChanged.emit(Qt.Horizontal, index.column(), index.column())
                return True
        return False

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == self.nameColumn:
                return 'Attribute'
            elif section == self.typeColumn:
                return 'Type'
            elif section == self.checkboxColumn:
                return all(self._checked)
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            return section
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if self._editable and index.column() == self.nameColumn:
            flags |= Qt.ItemIsEditable
        elif self._checkable and index.column() == self.checkboxColumn:
            flags |= Qt.ItemIsEditable
        return flags


class AttributeWithIndexModel(QIdentityProxyModel):
    # TODO: test this (DRAFT)
    def mapToSource(self, proxyIndex: QModelIndex) -> QModelIndex:
        if not proxyIndex.isValid():
            return QModelIndex()
        if proxyIndex.model() != self:
            return QModelIndex()
        proxyRow = proxyIndex.row()
        proxyColumn = proxyIndex.column()
        indexLevels = len(self.sourceModel().frameModel().shape.index)
        if proxyRow < indexLevels:
            return QModelIndex()
        return self.sourceModel().index(proxyRow - indexLevels, proxyColumn, proxyIndex.parent())

    def mapFromSource(self, sourceIndex: QModelIndex) -> QModelIndex:
        if not sourceIndex.isValid():
            return QModelIndex()
        if sourceIndex.model() != self.sourceModel():
            return QModelIndex()
        sourceRow = sourceIndex.row()
        sourceColumn = sourceIndex.column()
        indexLevels = len(self.sourceModel().frameModel().shape.index)
        return self.index(sourceRow + indexLevels, sourceColumn, sourceColumn.parent())

    def data(self, proxyIndex: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not proxyIndex.isValid():
            return None

        if role == Qt.DisplayRole or role == Qt.EditRole:
            if proxyIndex.column() == self.checkboxColumn:
                return None
            proxyRow: int = proxyIndex.row()
            proxyColumn: int = proxyIndex.column()

            indexes: List[str] = self.sourceModel().frameModel().shape.index
            indexTypes: List[Type] = self.sourceModel().frameModel().shape.indexTypes
            indexLevels: int = len(indexes)
            if proxyRow < indexLevels:
                if proxyColumn == self.sourceModel().nameColumn:
                    return indexes[proxyRow]
                if proxyColumn == self.sourceModel().typeColumn:
                    return indexTypes[proxyRow]
        return super().data(proxyIndex, role)

    def rowCount(self, parent: QModelIndex = ...) -> int:
        if parent.isValid():
            return 0
        return self.sourceModel().rowCount(parent) + len(self.sourceModel().frameModel().shape.index)

    def setData(self, index: QModelIndex, value: str, role: int = ...) -> bool:
        if not index.isValid():
            return False
        # indexes: List[str] = self.sourceModel().frameModel().shape.index
        # indexLevels: int = len(indexes)
        # if role == Qt.EditRole and index.row() < indexLevels:
        #     value = value.strip()
        #     # Edit a index
        #     if value:
        #         if indexLevels > 1:
        #             frame = self.sourceModel().frameModel().frame.getRawFrame() \
        #                 .index.set_names(value)
        return super().setData(index, value, role)

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        indexes: List[str] = self.sourceModel().frameModel().shape.index
        indexLevels: int = len(indexes)
        if index.row() < indexLevels:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return super().flags(index)


class AttributeProxyModel(AbstractAttributeModel, QSortFilterProxyModel,
                          metaclass=AttributeProxyModelMeta):
    """ Proxy model to filter attributes to show """

    def __init__(self, filterTypes: List[Type] = None, parent: QWidget = None):
        super().__init__(parent)
        self._filterTypes: Optional[List[Type]] = None
        self.setFilters(filterTypes)

    def filters(self) -> Optional[List[Type]]:
        return self._filterTypes

    def setFilters(self, filterTypes: List[Type]) -> None:
        self._filterTypes = filterTypes if (filterTypes and filterTypes != ALL_TYPES) else None

    def __isAcceptedByType(self, source_row: int, _: QModelIndex) -> bool:
        """ Returns True iff source_row has an accepted type """
        if self._filterTypes:
            rowType: Type = self.frameModel().shape.colTypes[source_row]
            return rowType in self._filterTypes
        return True

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        return self.__isAcceptedByType(source_row, source_parent) and \
               super().filterAcceptsRow(source_row, source_parent)

    @property
    def checkboxColumn(self) -> Optional[int]:
        return self.sourceModel().checkboxColumn

    @property
    def typeColumn(self) -> Optional[int]:
        return self.sourceModel().typeColumn

    @property
    def nameColumn(self) -> Optional[int]:
        return self.sourceModel().nameColumn

    def frameModel(self) -> Optional[FrameModel]:
        return self.sourceModel().frameModel()

    def setFrameModel(self, model: FrameModel) -> None:
        self.sourceModel().setFrameModel(model)

    @property
    def checked(self) -> Optional[List[int]]:
        return self.sourceModel().checked

    def setChecked(self, rows: List[int], value: bool) -> None:
        self.sourceModel().setChecked(rows, value)

    def setAllChecked(self, value: bool) -> None:
        """ Sets all proxy items check state to 'value'  """
        # Get all shown items rows in source model and set their value
        allIndexes = QItemSelection(
            self.index(0, self.checkboxColumn, QModelIndex()),
            self.index(self.rowCount() - 1, self.checkboxColumn, QModelIndex()))
        sourceIndexes: List[QModelIndex] = self.mapSelectionToSource(allIndexes).indexes()
        self.setChecked(list(map(lambda x: x.row(), sourceIndexes)), value)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        """ Redefined to handle selection by clicking on header """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole and section == self.checkboxColumn:
            # Return True if all visible items are checked
            checkedAttr = self.checked
            if not self.checked:
                # No item are checked in source model, so they are not checked in proxy
                return False
            if self.sourceModel().headerData(section, orientation, role) is True:
                # If all items are checked in source model then they are checked also in proxy
                return True
            # Check if all visible items are checked (mapSelectionToSource can be slow)
            allIndexes = QItemSelection(
                self.index(0, self.checkboxColumn, QModelIndex()),
                self.index(self.rowCount() - 1, self.checkboxColumn, QModelIndex()))
            sourceIndexes: List[QModelIndex] = self.mapSelectionToSource(allIndexes).indexes()
            return all(map(lambda x: x.row() in checkedAttr, sourceIndexes))
        return self.sourceModel().headerData(section, orientation, role)


class SearchableAttributeTableWidget(QWidget):
    def __init__(self, parent: QWidget = None,
                 checkable: bool = False, editable: bool = False,
                 showTypes: bool = False, filterTypes: List[Type] = None):
        super().__init__(parent)
        # Models
        model = AttributeTableModel(parent=self, checkable=checkable,
                                    editable=editable,
                                    showTypes=showTypes)
        self.__model: Optional[AttributeProxyModel] = None
        # Creates and set up a proxy model with 'model' as its source
        self.__setUpProxies(model, filterTypes)

        self.tableView = SignalTableView(parent=self)

        self.__searchBar = QLineEdit(self)
        self.__searchBar.setPlaceholderText('Search')
        searchLabel = QLabel('Attribute search', self)
        # titleLabel = QLabel('Attribute list')
        searchLayout = QHBoxLayout()
        # searchLayout.addWidget(titleLabel, 0, alignment=Qt.AlignRight)
        # searchLayout.addStretch(1)
        # searchLayout.addSpacing(200)
        searchLayout.addWidget(searchLabel, 1, alignment=Qt.AlignRight)
        searchLayout.addSpacing(30)
        searchLayout.addWidget(self.__searchBar, 0, alignment=Qt.AlignRight)

        # Connect search and checkbox click
        self.__searchBar.textChanged.connect(self.setFilterRegularExpression)
        self.__searchBar.textChanged.connect(self.refreshHeaderCheckbox)

        layout = QVBoxLayout()
        layout.addLayout(searchLayout)
        layout.addWidget(self.tableView)
        self.setLayout(layout)

    def __setUpProxies(self, model: AttributeTableModel, filterTypes: List[Type]) -> None:
        """ Creates and sets up a proxyModel with 'model' as its source. The proxy will be searchable
        and will filter types """
        # First create a new proxy if None is set
        if not self.__model:
            self.__model: AttributeProxyModel = AttributeProxyModel(parent=self)
        # Add type filter and search
        self.__model.setSourceModel(model)
        self.__model.setFilterKeyColumn(model.nameColumn)
        self.__model.setFilters(filterTypes)

    def model(self) -> AttributeProxyModel:
        return self.__model

    def setAttributeModel(self, model: AttributeTableModel, filterTypes: List[Type] = None) -> None:
        """
        Sets a custom AttributeTableModel. If the source frame is present it also updates view.
        This method is provided as an alternative to building everything in the constructor.
        """
        # Set up a proxy for search and type-filtering
        self.__setUpProxies(model, filterTypes)
        if self.__model.frameModel():
            # The model already have the frameModel set
            self.setSourceFrameModel(self.__model.frameModel())

    def setSourceFrameModel(self, source: FrameModel) -> None:
        """ Adds the frame mode in the current AttributeModel and updates the view  """
        self.__model.setFrameModel(source)
        viewModel = self.tableView.model()
        if viewModel is None:
            # When no model is set in view
            # Set model in the view
            self.tableView.setModel(self.__model)
            # Set sections stretch and alignment
            hh = self.tableView.horizontalHeader()
            hh.setStretchLastSection(False)
            hh.setSectionsClickable(True)
            checkPos: Optional[int] = self.__model.checkboxColumn
            if checkPos is not None:
                hh.resizeSection(checkPos, 5)
                hh.setSectionResizeMode(checkPos, QHeaderView.Fixed)
            hh.setSectionResizeMode(self.__model.nameColumn, QHeaderView.Stretch)
            if self.__model.typeColumn is not None:
                hh.setSectionResizeMode(self.__model.typeColumn, QHeaderView.Stretch)
            self.tableView.verticalHeader().setDefaultAlignment(Qt.AlignHCenter)
            # Set delegate for checkbox
            if self.__model.checkboxColumn is not None:
                self.tableView.setItemDelegateForColumn(self.__model.checkboxColumn,
                                                        BooleanBoxDelegate(self))
            hh.sectionClicked.connect(self.__model.onHeaderClicked)

    @Slot(str)
    def setFilterRegularExpression(self, pattern: str) -> None:
        """ Custom slot to set case insensitivity """
        if not self.__model:
            return
        exp = QRegularExpression(pattern, options=QRegularExpression.CaseInsensitiveOption)
        self.__model.setFilterRegularExpression(exp)

    @Slot()
    def refreshHeaderCheckbox(self) -> None:
        """ Emits headerDataChanged on the checkbox column if present """
        if not self.__model:
            return
        section = self.__model.checkboxColumn
        if section is not None:
            self.__model.headerDataChanged.emit(Qt.Horizontal, section, section)


class SignalTableView(QTableView):
    selectedRowChanged = Signal((int, int), (str, str))

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.setAlternatingRowColors(True)

    def selectionChanged(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        """ Emit signal when current selection changes """
        super().selectionChanged(selected, deselected)
        current: QModelIndex = selected.indexes()[0] if selected.indexes() else QModelIndex()
        previous: QModelIndex = deselected.indexes()[0] if deselected.indexes() else QModelIndex()
        crow: int = -1
        prow: int = -1
        cdata: str = current.data(Qt.DisplayRole)
        pdata: str = previous.data(Qt.DisplayRole)
        if isinstance(self.model(), QAbstractProxyModel):
            current = self.model().mapToSource(current) if current.isValid() else current
            previous = self.model().mapToSource(previous) if previous.isValid() else previous
        if current.isValid():
            crow = current.row()
        if previous.isValid():
            prow = previous.row()
        self.selectedRowChanged[int, int].emit(crow, prow)
        # If data is string, also emit the signal with string
        if isinstance(cdata, str):
            self.selectedRowChanged[str, str].emit(cdata, pdata)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        selection: List[QModelIndex] = self.selectedIndexes()
        if selection:
            previousRow: QModelIndex = selection[0].row() if selection and selection[0].isValid() else -1
            index = self.indexAt(event.pos())
            if not index.isValid():
                self.selectedRowChanged.emit(-1, previousRow)
        super().mouseReleaseEvent(event)


class BooleanBoxDelegate(QStyledItemDelegate):
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        return None

    def paint(self, painter: QtGui.QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        checked: bool = index.data(Qt.DisplayRole)

        options = QStyleOptionButton()
        if (index.flags() & Qt.ItemIsEditable) > 0:
            options.state |= QStyle.State_Enabled
        else:
            options.state |= QStyle.State_ReadOnly
        if checked:
            options.state |= QStyle.State_On
        else:
            options.state |= QStyle.State_Off

        options.rect = self.__getCheckboxRect(option)
        if not (index.flags() & Qt.ItemIsEditable):
            options.state |= QStyle.State_ReadOnly
        QApplication.style().drawControl(QStyle.CE_CheckBox, options, painter)

    def editorEvent(self, event: QEvent, model: QAbstractItemModel, option: QStyleOptionViewItem,
                    index: QModelIndex) -> bool:
        if not (index.flags() & Qt.ItemIsEditable) > 0:
            return False
        if event.type() == QEvent.MouseButtonRelease:
            if event.button() != Qt.LeftButton:
                # or not self.__getCheckboxRect(option).contains(event.pos()):
                return False
            if event.type() == QEvent.MouseButtonDblClick:
                return True
        elif event.type() == QEvent.KeyPress:
            if event.key() != Qt.Key_Space and event.key() != Qt.Key_Select:
                return False
        else:
            return False
        self.setModelData(None, model, index)
        return True  # super().editorEvent(event, model, option, index)

    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex) -> None:
        model.setData(index, not index.data(Qt.EditRole))

    @staticmethod
    def __getCheckboxRect(option: QStyleOptionViewItem) -> QRect:
        check_options = QStyleOptionButton()
        check_rect = QApplication.style().subElementRect(QStyle.SE_CheckBoxIndicator, check_options,
                                                         None)
        check_point = QPoint(option.rect.x() + option.rect.width() / 2 - check_rect.width() / 2,
                             option.rect.y() + option.rect.height() / 2 - check_rect.height() / 2)
        return QRect(check_point, check_rect.size())


class TableHeader(QHeaderView):
    # TODO: use this to paint a checkbox in header
    def __init__(self, checkboxSection: Optional[int], orientation: Qt.Orientation, parent=None):
        super().__init__(orientation, parent)
        self.__checkboxSection = checkboxSection
        self.setSectionsClickable(True)

    def paintSection(self, painter: QPainter, rect: QRect, logicalIndex: int) -> None:
        if not self.__checkboxSection:
            return super().paintSection(painter, rect, logicalIndex)
        painter.save()
        super().paintSection(painter, rect, logicalIndex)
        painter.restore()
        if self.__checkboxSection == logicalIndex:
            option = QStyleOptionButton()
            option.rect = QRect(10, 10, 10, 10)
            option.state = QStyle.State_Enabled | QStyle.State_Active
            if self.__isChecked:
                option.state |= QStyle.State_On
            else:
                option.state |= QStyle.State_Off
            QApplication.style().drawControl(QStyle.CE_CheckBox, option, painter)
