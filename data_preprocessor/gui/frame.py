import logging
from enum import Enum
from typing import Any, List, Union, Dict, Tuple

from PySide2 import QtGui
from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal, Slot, QAbstractItemModel, \
    QSortFilterProxyModel, QBasicTimer, QTimerEvent, QItemSelection, QThreadPool
from PySide2.QtWidgets import QWidget, QTableView, QLineEdit, QVBoxLayout, QHeaderView, QLabel, \
    QHBoxLayout

from data_preprocessor.data import Frame, Shape
from data_preprocessor.data.types import Types
# New role to return raw data from header
from data_preprocessor.operation.computations.statistics import AttributeStatistics, Hist
from data_preprocessor.threads import Worker


class MyRoles(Enum):
    DataRole = Qt.UserRole


class FrameModel(QAbstractTableModel):
    """ Table model for a single dataframe """

    DataRole = MyRoles.DataRole
    COL_BATCH_SIZE = 50

    statisticsComputed = Signal(tuple)
    statisticsError = Signal(tuple)

    def __init__(self, parent: QWidget = None, frame: Frame = Frame(), nrows: int = 10):
        super().__init__(parent)
        self.__frame: Frame = frame
        self.__shape: Shape = self.__frame.shape
        self.__n_rows: int = nrows
        self.__loadedCols: int = self.COL_BATCH_SIZE
        # Dictionary { attributeIndex: value }
        self._statistics: Dict[int, Dict[str, object]] = dict()
        self._histogram: Dict[int, Dict[Any, int]] = dict()

    @property
    def frame(self) -> Frame:
        return self.__frame

    def setFrame(self, frame: Frame) -> None:
        self.beginResetModel()
        self.__frame = frame
        self.__shape: Shape = self.__frame.shape
        self._statistics = dict()
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return self.__frame.nRows if self.__frame.nRows < self.__n_rows else self.__n_rows

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        allCols = self.__shape.n_columns
        if allCols < self.__loadedCols:
            return allCols
        return self.__loadedCols

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if index.isValid() and index.row() < self.__n_rows:
            if role == Qt.DisplayRole:
                return str(self.__frame.at((index.row(), index.column())))
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self.__shape.col_names[section] + '\n' + self.__shape.col_types[section].value
            elif role == FrameModel.DataRole.value:
                return self.__shape.col_names[section], self.__shape.col_types[section]
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            if self.__shape.has_index():
                return self.__frame.index[section]
        return None

    def setHeaderData(self, section: int, orientation: Qt.Orientation, value: Any, role: int = ...) \
            -> bool:
        """ Change column name """
        if orientation == Qt.Horizontal and role == Qt.EditRole and section < self.columnCount():
            names = self.__frame.colnames
            names[section] = value
            self.__frame = self.__frame.rename({self.headerData(section, orientation,
                                                                FrameModel.DataRole.value)[0]: value})
            self.__shape.col_names[section] = value
            self.headerDataChanged.emit(orientation, section, section)
            return True
        return False

    def canFetchMore(self, parent: QModelIndex) -> bool:
        """ Returns True if more columns should be displayed, False otherwise """
        if self.__shape.n_columns > self.__loadedCols:
            return True
        return False

    def fetchMore(self, parent: QModelIndex):
        remainder = self.__shape.n_columns - self.__loadedCols
        colsToFetch = min(remainder, self.COL_BATCH_SIZE)
        self.beginInsertColumns(parent, self.__loadedCols, self.__loadedCols + colsToFetch - 1)
        self.__loadedCols += colsToFetch
        self.endInsertColumns()

    @property
    def statistics(self) -> Dict[int, Dict[str, object]]:
        return self._statistics

    @property
    def histogram(self) -> Dict[int, Dict[Any, int]]:
        return self._histogram

    def computeStatistics(self, attribute: int) -> None:
        """ Compute statistics for a given attribute """
        stats = AttributeStatistics()
        attType = self.__shape.col_types[attribute]
        stats.setOptions(attribute=attribute)
        statWorker = Worker(stats, args=(self.__frame,), identifier=(attribute, attType, 'stat'))
        statWorker.signals.result.connect(self.onWorkerSuccess, Qt.DirectConnection)
        statWorker.signals.error.connect(self.onWorkerError, Qt.DirectConnection)
        QThreadPool.globalInstance().start(statWorker)

    def computeHistogram(self, attribute: int, histBins: int) -> None:
        hist = Hist()
        attType = self.__shape.col_types[attribute]
        hist.setOptions(attribute=attribute, attType=attType, bins=histBins)
        histWorker = Worker(hist, args=(self.__frame,), identifier=(attribute, attType, 'hist'))
        histWorker.signals.result.connect(self.onWorkerSuccess, Qt.DirectConnection)
        histWorker.signals.error.connect(self.onWorkerError, Qt.DirectConnection)
        QThreadPool.globalInstance().start(histWorker)

    @Slot(object, object)
    def onWorkerSuccess(self, identifier: Tuple[int, Types, str], result: Dict[Any, Any]) -> None:
        attribute, attType, mode = identifier
        if mode == 'stat':
            self._statistics[attribute] = result
            logging.info('Statistics computation succeeded')
        elif mode == 'hist':
            self._histogram[attribute] = result
            logging.info('Histogram computation succeeded')
        self.statisticsComputed.emit(identifier)

    @Slot(object, tuple)
    def onWorkerError(self, identifier: Tuple[int, Types, str],
                      error: Tuple[type, Exception, str]) -> None:
        logging.error('Statistics computation failed with {}: {}\n{}'.format(*error))
        self.statisticsError.emit(identifier)


class AttributeTableModel(QAbstractTableModel):
    def __init__(self, parent: QWidget = None, checkable: bool = False,
                 editable: bool = False):
        """ Creates a tablemodel to hold attributes list

        :param parent: parent widget
        :param checkable: whether an additional column with checkbox must be added
        :param editable: whether the model must support attribute renaming
        """
        super().__init__(parent)
        self._checkable: bool = checkable
        self._editable: bool = editable
        # Keeps track of checked items
        self._checked: List[bool] = list()
        self._sourceModel: QAbstractItemModel = None
        self._statistics: Dict[str, Dict[str, object]] = dict()

    @property
    def checkbox_pos(self) -> Union[int, None]:
        """
        Return the column index for checkbox
        """
        if self._checkable:
            return 0
        else:
            return None

    @property
    def type_pos(self) -> int:
        """ Return the column index for type """
        if self._checkable:
            return 2
        else:
            return 1

    @property
    def name_pos(self) -> int:
        """ Return the column index for name """
        if self._checkable:
            return 1
        else:
            return 0

    def sourceModel(self) -> FrameModel:
        return self._sourceModel

    # Getter and setter for checkbox
    def checkedAttributes(self) -> List[int]:
        """ Get selected rows if the model is checkable """
        return [i for i, v in enumerate(self._checked) if v] if self._checkable else None

    def setSourceModel(self, sourceModel: QAbstractItemModel) -> None:
        if self._sourceModel is sourceModel:
            return

        self.beginResetModel()

        # Disconnect this model from old model' signals
        if self._sourceModel:
            self._sourceModel.disconnect(self)

        # Update checked state
        if self._checkable:
            self._checked = [False] * sourceModel.columnCount(QModelIndex())

        self._sourceModel = sourceModel

        # Connect to new model
        # TODO: test if this is enough. Also some of these are NOT slots
        self._sourceModel.modelAboutToBeReset.connect(self.beginResetModel)
        self._sourceModel.modelReset.connect(self.endResetModel)
        self._sourceModel.headerDataChanged.connect(self.onHeaderChanged)
        self._sourceModel.columnsAboutToBeInserted.connect(self.onColumnsAboutToBeInserted)
        self._sourceModel.columnsAboutToBeMoved.connect(self.onColumnsAboutToBeMoved)
        self._sourceModel.columnsAboutToBeRemoved.connect(self.onColumnsAboutToBeRemoved)
        self._sourceModel.columnsInserted.connect(self.endInsertRows)
        self._sourceModel.columnsMoved.connect(self.endMoveRows)
        self._sourceModel.columnsRemoved.connect(self.endRemoveRows)

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
            self.dataChanged.emit(self.index(sec1, self.name_pos),
                                  self.index(sec2, self.name_pos))

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return self._sourceModel.columnCount()

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return 3 if self._checkable else 2

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if not index.isValid():
            return None

        if (role == Qt.DisplayRole or role == Qt.EditRole) and index.column() != self.checkbox_pos:
            name: str
            col_type: Types
            name, col_type = self._sourceModel.headerData(index.row(), orientation=Qt.Horizontal,
                                                          role=FrameModel.DataRole.value)
            value = None
            if index.column() == self.name_pos:
                value = name
            elif index.column() == self.type_pos:
                value = col_type.value
            return value
        # Return the correct value for checkbox
        elif role == Qt.CheckStateRole and index.column() == self.checkbox_pos:
            if self._checked[index.row()]:
                return Qt.Checked
            else:
                return Qt.Unchecked
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        return None

    def setData(self, index: QModelIndex, value: Any, role: int = ...) -> bool:
        # NOTE: does not support changing type for now
        if not index.isValid():
            return False

        # Change attribute name
        if role == Qt.EditRole and index.column() == self.name_pos and value != index.data(
                Qt.DisplayRole):
            return self._sourceModel.setHeaderData(index.row(), Qt.Horizontal, value, Qt.EditRole)
        # Toggle checkbox state
        elif role == Qt.CheckStateRole and index.column() == self.checkbox_pos:
            i: int = index.row()
            self._checked[i] = not self._checked[i]
            self.dataChanged.emit(index, index)
            return True
        return False

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == self.name_pos:
                return 'Attribute'
            elif section == self.type_pos:
                return 'Type'
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if self._editable and index.column() == self.name_pos:
            flags |= Qt.ItemIsEditable
        elif self._checkable and index.column() == self.checkbox_pos:
            flags |= Qt.ItemIsUserCheckable
        return flags

    def canFetchMore(self, parent: QModelIndex) -> bool:
        return self._sourceModel.canFetchMore(parent)

    def fetchMore(self, parent: QModelIndex) -> None:
        self._sourceModel.fetchMore(parent)
        if self._checkable:
            new_rows = self.rowCount() - len(self._checked)
            self._checked.extend([False] * new_rows)


class AttributeTableModelFilter(QSortFilterProxyModel):
    def __init__(self, filterTypes: List[Types], parent: QWidget = None):
        super().__init__(parent)
        self._filterTypes = filterTypes

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        index = self.sourceModel().index(source_row, self.sourceModel().type_pos, source_parent)

        type_data: str = self.sourceModel().data(index, Qt.DisplayRole)
        if Types(type_data) in self._filterTypes:
            return True
        return False


class SearchableAttributeTableWidget(QWidget):
    def __init__(self, parent: QWidget = None, checkable: bool = False, editable: bool = False):
        super().__init__(parent)
        self.__model = AttributeTableModel(parent=self, checkable=checkable, editable=editable)
        self.tableView = IncrementalAttributeTableView(parent=self, namecol=self.__model.name_pos)
        self._tableModel = QSortFilterProxyModel(self)
        self._tableModel.setSourceModel(self.__model)
        self._tableModel.setFilterCaseSensitivity(Qt.CaseInsensitive)

        self._searchBar = QLineEdit(self)
        self._searchBar.setPlaceholderText('Search')
        searchLabel = QLabel('Attribute search')
        titleLabel = QLabel('Attribute list')
        searchLayout = QHBoxLayout()
        searchLayout.addWidget(titleLabel, 0, alignment=Qt.AlignRight)
        searchLayout.addStretch(1)
        searchLayout.addWidget(searchLabel, 0, alignment=Qt.AlignLeft)
        searchLayout.addSpacing(20)
        searchLayout.addWidget(self._searchBar, 0, alignment=Qt.AlignLeft)

        layout = QVBoxLayout()
        layout.addLayout(searchLayout)
        layout.addWidget(self.tableView)
        self.setLayout(layout)

    def model(self) -> AttributeTableModel:
        return self.__model

    def setSourceFrameModel(self, source: FrameModel) -> None:
        self.__model.setSourceModel(source)
        if self.tableView.model() is not self._tableModel:
            self.tableView.setModel(self._tableModel)
            hh = self.tableView.horizontalHeader()
            check_pos = self.__model.checkbox_pos
            if check_pos:
                hh.resizeSection(check_pos, 10)
                hh.setSectionResizeMode(check_pos, QHeaderView.Fixed)
            hh.setSectionResizeMode(self.__model.name_pos, QHeaderView.Stretch)
            hh.setSectionResizeMode(self.__model.type_pos, QHeaderView.Fixed)
            hh.setStretchLastSection(False)
            self._tableModel.setFilterKeyColumn(self.__model.name_pos)
            self.tableView.setHorizontalHeader(hh)
            self._searchBar.textChanged.connect(self._tableModel.setFilterRegExp)


class IncrementalAttributeTableView(QTableView):
    selectedAttributeChanged = Signal(int)

    def __init__(self, namecol: int, period: int = 50, parent: QWidget = None):
        super().__init__(parent)
        self.__timer = QBasicTimer()
        self.__timerPeriodMs = period
        self.__attNameColumn = namecol
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)

    def setModel(self, model: AttributeTableModel) -> None:
        """ Reimplemented to start fetch timer """
        if self.__timer.isActive():
            self.__timer.stop()
            logging.debug('Model about to be set. Fetch timer stopped')
        super().setModel(model)
        # Add timer to periodically fetch more rows
        self.__timer.start(self.__timerPeriodMs, self)
        logging.debug('Model set. Fetch timer started')

    def timerEvent(self, event: QTimerEvent) -> None:
        if event.timerId() == self.__timer.timerId():
            more = self.__fetchMoreRows()
            if not more:
                self.__timer.stop()
                logging.debug('Fetch timer stopped')
        super().timerEvent(event)

    def reset(self) -> None:
        """ Reimplemented to start fetch timer when model is reset """
        # Stop to avoid problems while model is reset
        if self.__timer.isActive():
            self.__timer.stop()
            logging.debug('Model about to be reset. Fetch timer stopped')
        super().reset()
        # Restart timer
        self.__timer.start(self.__timerPeriodMs, self)
        logging.debug('Model reset. Fetch timer started')

    def __fetchMoreRows(self, parent: QModelIndex = QModelIndex()) -> bool:
        """
        Tries to fetch more data from the model

        :return True if new data were fetched, False otherwise
        """
        model = self.model()
        if model is None or not model.canFetchMore(parent):
            return False
        model.fetchMore(parent)
        return True

    def selectionChanged(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        """ Emit signal when current selection changes """
        super().selectionChanged(selected, deselected)
        current: QModelIndex = selected.indexes()[0] if selected.indexes() else QModelIndex()
        if current.isValid():
            self.selectedAttributeChanged.emit(self.model().mapToSource(current).row())
        else:
            self.selectedAttributeChanged.emit(-1)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        index = self.indexAt(event.pos())
        if not index.isValid():
            self.selectedAttributeChanged.emit(-1)

# class ShapeAttributeNamesListModel(QAbstractListModel):
#     def __init__(self, shape: Shape, parent: QWidget = None):
#         super().__init__(parent)
#         self.__shape = shape if shape else Shape()
#
#     def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
#         if parent.isValid():
#             return 0
#         return self.__shape.n_columns
#
#     def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Optional[str]:
#         if index.isValid():
#             return self.__shape.col_names[index.row()]
#         return None
