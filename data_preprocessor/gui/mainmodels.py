import abc
import logging
from enum import Enum
from typing import Any, List, Union, Dict, Tuple, Optional

from PySide2 import QtGui
from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal, Slot, QAbstractItemModel, \
    QSortFilterProxyModel, QBasicTimer, QTimerEvent, QItemSelection, QThreadPool, QEvent, QRect, QPoint, \
    QRegularExpression
from PySide2.QtGui import QPainter
from PySide2.QtWidgets import QWidget, QTableView, QLineEdit, QVBoxLayout, QHeaderView, QLabel, \
    QHBoxLayout, QStyleOptionViewItem, QStyleOptionButton, QStyle, QApplication, \
    QStyledItemDelegate

from data_preprocessor.data import Frame, Shape
from data_preprocessor.data.types import Types, ALL_TYPES
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

    def __init__(self, parent: QWidget = None, frame: Union[Frame, Shape] = Frame(), nrows: int = 10):
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
        self.__n_rows: int = nrows
        # Change this to COL_BATCH_SIZE to reactivate fetchMore
        self.__loadedCols: int = self.__shape.n_columns
        # Dictionary { attributeIndex: value }
        self._statistics: Dict[int, Dict[str, object]] = dict()
        self._histogram: Dict[int, Dict[Any, int]] = dict()
        self.name: str = ''

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
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return self.__frame.nRows if self.__frame.nRows < self.__n_rows else self.__n_rows

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        allCols = self.__shape.n_columns
        # NOTE: incremental loading is disabled
        # if allCols < self.__loadedCols:
        #     return allCols
        # return self.__loadedCols
        return allCols

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
        self._frameModel.modelAboutToBeReset.connect(self.beginResetModel)
        self._frameModel.modelReset.connect(self.endResetModel)
        self._frameModel.headerDataChanged.connect(self.onHeaderChanged)
        self._frameModel.columnsAboutToBeInserted.connect(self.onColumnsAboutToBeInserted)
        self._frameModel.columnsAboutToBeMoved.connect(self.onColumnsAboutToBeMoved)
        self._frameModel.columnsAboutToBeRemoved.connect(self.onColumnsAboutToBeRemoved)
        self._frameModel.columnsInserted.connect(self.endInsertRows)
        self._frameModel.columnsMoved.connect(self.endMoveRows)
        self._frameModel.columnsRemoved.connect(self.endRemoveRows)

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
        if parent.isValid():
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
            col_type: Types
            name, col_type = self._frameModel.headerData(index.row(), orientation=Qt.Horizontal,
                                                         role=FrameModel.DataRole.value)
            value = None
            if index.column() == self.nameColumn:
                value = name
            elif index.column() == self.typeColumn:
                value = col_type.value
            return value
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        return None

    def setData(self, index: QModelIndex, value: Any, role: int = ...) -> bool:
        # NOTE: does not support changing type for now
        if not index.isValid():
            return False

        if role == Qt.EditRole:
            # Change attribute name
            if index.column() == self.nameColumn and value != index.data(Qt.DisplayRole):
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

    def canFetchMore(self, parent: QModelIndex) -> bool:
        return self._frameModel.canFetchMore(parent)

    def fetchMore(self, parent: QModelIndex) -> None:
        self._frameModel.fetchMore(parent)
        if self._checkable:
            new_rows = self.rowCount() - len(self._checked)
            self._checked.extend([False] * new_rows)


class AttributeProxyModel(AbstractAttributeModel, QSortFilterProxyModel,
                          metaclass=AttributeProxyModelMeta):
    """ Proxy model to filter attributes to show """

    def __init__(self, filterTypes: List[Types], parent: QWidget = None):
        super().__init__(parent)
        self._filterTypes: Optional[List[Types]] = filterTypes if (filterTypes and filterTypes !=
                                                                   ALL_TYPES) else None

    def __isAcceptedByType(self, source_row: int, _: QModelIndex) -> bool:
        """ Returns True iff source_row has an accepted type """
        if self._filterTypes:
            rowType: Types = self.frameModel().shape.col_types[source_row]
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
                 showTypes: bool = False, filterTypes: List[Types] = None):
        super().__init__(parent)
        # Models
        model = AttributeTableModel(parent=self, checkable=checkable,
                                    editable=editable,
                                    showTypes=showTypes)
        self.__model: AttributeProxyModel = self.__setUpProxies(model, filterTypes)

        self.tableView = IncrementalAttributeTableView(parent=self)

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

        layout = QVBoxLayout()
        layout.addLayout(searchLayout)
        layout.addWidget(self.tableView)
        self.setLayout(layout)

    @staticmethod
    def __setUpProxies(model: AttributeTableModel, filterTypes: List[Types]) -> AttributeTableModel:
        # Add type filter and search
        model1 = AttributeProxyModel(filterTypes=filterTypes,
                                     parent=model)
        model1.setSourceModel(model)
        model1.setFilterKeyColumn(model.nameColumn)
        return model1

    def model(self) -> AttributeProxyModel:
        return self.__model

    def setAttributeModel(self, model: AttributeTableModel, filterTypes: List[Types] = None) -> None:
        """
        Sets a custom AttributeTableModel. If the source frame is present it also updates view.
        This method is provided as an alternative to building everything in the constructor.
        """
        if self.__model:
            self.__model.deleteLater()  # Delete old model and its proxy
        self.__model: AttributeProxyModel = self.__setUpProxies(model, filterTypes)
        if self.__model.frameModel():
            # The model already have the frameModel set
            self.setSourceFrameModel(self.__model.frameModel())

    def setSourceFrameModel(self, source: FrameModel) -> None:
        """ Adds the frame mode in the current AttributeModel and updates the view  """
        self.__model.setFrameModel(source)
        oldViewModel = self.tableView.model()
        if oldViewModel is not self.__model:
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
            # Connect search and checkbox click
            self.__searchBar.textChanged.connect(self.setFilterRegularExpression)
            self.__searchBar.textChanged.connect(self.refreshHeaderCheckbox)
            hh.sectionClicked.connect(self.__model.onHeaderClicked)
            if oldViewModel:
                oldViewModel.deleteLater()

    @Slot(str)
    def setFilterRegularExpression(self, pattern: str) -> None:
        """ Custom slot to set case insensitivity """
        exp = QRegularExpression(pattern, options=QRegularExpression.CaseInsensitiveOption)
        self.__model.setFilterRegularExpression(exp)

    @Slot()
    def refreshHeaderCheckbox(self) -> None:
        """ Emits headerDataChanged on the checkbox column if present """
        section = self.__model.checkboxColumn
        if section is not None:
            self.__model.headerDataChanged.emit(Qt.Horizontal, section, section)


class IncrementalAttributeTableView(QTableView):
    selectedAttributeChanged = Signal(int)

    def __init__(self, period: int = 0, parent: QWidget = None):
        super().__init__(parent)
        self.__timer = QBasicTimer()
        self.__timerPeriodMs = period
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)

    def setModel(self, model: AttributeTableModel) -> None:
        """ Reimplemented to start fetch timer """
        if self.__timer.isActive():
            self.__timer.stop()
            logging.debug('Model about to be set. Fetch timer stopped')
        super().setModel(model)
        # Add timer to periodically fetch more rows
        if self.__timerPeriodMs:
            self.__timer.start(self.__timerPeriodMs, self)
            logging.debug('Model set. Fetch timer started')
        else:
            logging.debug('Model set. Timer not activated (period=0)')
        checkable: int = model.checkboxColumn
        if checkable is not None:
            self.setItemDelegateForColumn(checkable, BooleanBoxDelegate(self))

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
        if self.__timerPeriodMs:
            # Restart timer
            self.__timer.start(self.__timerPeriodMs, self)
            logging.debug('Model reset. Fetch timer started')
        else:
            logging.debug('Model reset. Timer not activated (period=0)')

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
            index: QModelIndex = self.model().mapToSource(current)
            row: int = index.row()
            self.selectedAttributeChanged.emit(row)
        else:
            self.selectedAttributeChanged.emit(-1)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        index = self.indexAt(event.pos())
        if not index.isValid():
            self.selectedAttributeChanged.emit(-1)


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
