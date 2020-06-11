import logging
from enum import Enum
from typing import Any, List, Union, Dict, Tuple, Optional

from PySide2 import QtGui
from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal, Slot, QAbstractItemModel, \
    QSortFilterProxyModel, QBasicTimer, QTimerEvent, QItemSelection, QThreadPool, QEvent, QRect, QPoint
from PySide2.QtGui import QPainter
from PySide2.QtWidgets import QWidget, QTableView, QLineEdit, QVBoxLayout, QHeaderView, QLabel, \
    QHBoxLayout, QStyleOptionViewItem, QStyleOptionButton, QStyle, QApplication, \
    QStyledItemDelegate

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


class AttributeTableModel(QAbstractTableModel):
    def __init__(self, parent: QWidget = None, checkable: bool = False,
                 editable: bool = False, showTypes: bool = True):
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
        self._sourceModel: QAbstractItemModel = None

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
        if self._showTypes:
            if self._checkable:
                return 2
            else:
                return 1
        else:
            return None

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
    @property
    def checkedAttributes(self) -> List[int]:
        """ Get selected rows if the model is checkable """
        return [i for i, v in enumerate(self._checked) if v] if self._checkable else None

    @checkedAttributes.setter
    def checkedAttributes(self, values: List[int]) -> None:
        if values:
            for index in values:
                self._checked[index] = True
        else:
            self._checked = [False] * self.rowCount()
        for v in values:
            qindex = self.index(v, self.checkbox_pos, QModelIndex())
            self.dataChanged.emit(qindex, qindex, [Qt.DisplayRole, Qt.EditRole])

    def setAllChecked(self, value: bool) -> None:
        """ Set all rows checked or unchecked """
        self.beginResetModel()
        if value is True:
            self._checked = [True] * self.rowCount()
        else:
            self._checked = [False] * self.rowCount()
        self.endResetModel()

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
            if index.column() == self.checkbox_pos:
                return self._checked[index.row()]
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
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        return None

    def setData(self, index: QModelIndex, value: Any, role: int = ...) -> bool:
        # NOTE: does not support changing type for now
        if not index.isValid():
            return False

        if role == Qt.EditRole:
            # Change attribute name
            if index.column() == self.name_pos and value != index.data(Qt.DisplayRole):
                return self._sourceModel.setHeaderData(index.row(), Qt.Horizontal, value, Qt.EditRole)
            # Toggle checkbox state
            elif index.column() == self.checkbox_pos:
                i: int = index.row()
                self._checked[i] = value
                self.dataChanged.emit(index, index)
                self.headerDataChanged.emit(Qt.Horizontal, index.column(), index.column())
                return True
        return False

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == self.name_pos:
                return 'Attribute'
            elif section == self.type_pos:
                return 'Type'
            elif section == self.checkbox_pos:
                return all(self._checked)
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            return section
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if self._editable and index.column() == self.name_pos:
            flags |= Qt.ItemIsEditable
        elif self._checkable and index.column() == self.checkbox_pos:
            flags |= Qt.ItemIsEditable
        return flags

    def canFetchMore(self, parent: QModelIndex) -> bool:
        return self._sourceModel.canFetchMore(parent)

    def fetchMore(self, parent: QModelIndex) -> None:
        self._sourceModel.fetchMore(parent)
        if self._checkable:
            new_rows = self.rowCount() - len(self._checked)
            self._checked.extend([False] * new_rows)

    @Slot(int)
    def onHeaderClicked(self, section: int) -> None:
        if section == self.checkbox_pos:
            checked = self.headerData(section, Qt.Horizontal, Qt.DisplayRole)
            if checked is True:
                self.setAllChecked(False)
            else:
                self.setAllChecked(True)


class TypeFilteredTableModel(QSortFilterProxyModel):
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
    def __init__(self, parent: QWidget = None, checkable: bool = False, editable: bool = False,
                 showTypes: bool = False, filterTypes: List[Types] = None):
        super().__init__(parent)
        self.__typeFiltered = bool(filterTypes)
        self.__model = AttributeTableModel(parent=self, checkable=checkable, editable=editable,
                                           showTypes=showTypes)
        self.tableView = IncrementalAttributeTableView(parent=self, namecol=self.__model.name_pos)
        typeFilteredModel = self.__setupFilteredModel(filterTypes)
        self._searchableModel = QSortFilterProxyModel(self)
        self._searchableModel.setSourceModel(typeFilteredModel)
        self._searchableModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        # Table Header
        # hh = TableHeader(self.__model.checkbox_pos, Qt.Horizontal, self.tableView)
        # self.tableView.setHorizontalHeader(hh)
        # hh.show()

        self._searchBar = QLineEdit(self)
        self._searchBar.setPlaceholderText('Search')
        searchLabel = QLabel('Attribute search', self)
        # titleLabel = QLabel('Attribute list')
        searchLayout = QHBoxLayout()
        # searchLayout.addWidget(titleLabel, 0, alignment=Qt.AlignRight)
        # searchLayout.addStretch(1)
        # searchLayout.addSpacing(200)
        searchLayout.addWidget(searchLabel, 1, alignment=Qt.AlignRight)
        searchLayout.addSpacing(30)
        searchLayout.addWidget(self._searchBar, 0, alignment=Qt.AlignRight)

        layout = QVBoxLayout()
        layout.addLayout(searchLayout)
        layout.addWidget(self.tableView)
        self.setLayout(layout)

    def __setupFilteredModel(self, typesToShow: List[Types]) -> QAbstractItemModel:
        typesToShow: List[Types] = typesToShow if typesToShow else list()
        if typesToShow:
            typeFilteredModel = TypeFilteredTableModel(typesToShow, self)
            typeFilteredModel.setSourceModel(self.__model)
            return typeFilteredModel
        return self.__model

    def model(self) -> AttributeTableModel:
        return self.__model

    def setModel(self, model: AttributeTableModel, filterTypes: List[Types] = None) -> None:
        """
        Sets a custom AttributeTableModel. If the source frame is present it also updates view.
        This method is provided as an alternative to building everything in the constructor.
        """
        self.__typeFiltered = bool(filterTypes)
        if self.tableView:
            oldView = self.tableView
            self.tableView = IncrementalAttributeTableView(parent=self, namecol=model.name_pos)
            self.layout().replaceWidget(oldView, self.tableView)
            oldView.deleteLater()
        if self.__model:
            self.__model.deleteLater()
        self.__model = model
        typeFilteredModel = self.__setupFilteredModel(filterTypes)
        self._searchableModel.setSourceModel(typeFilteredModel)
        if self.__model.sourceModel():
            self.setSourceFrameModel(self.__model.sourceModel())
        # hh = TableHeader(model.checkbox_pos, Qt.Horizontal, self.tableView)
        # self.tableView.setHorizontalHeader(hh)
        # hh.sectionClicked.connect(self.__model.onHeaderClicked)
        # hh.show()

    def setSourceFrameModel(self, source: FrameModel) -> None:
        self.__model.setSourceModel(source)
        if self.tableView.model() is not self._searchableModel:
            self.tableView.setModel(self._searchableModel, filtered=self.__typeFiltered)
            check_pos = self.__model.checkbox_pos
            hh = self.tableView.horizontalHeader()
            hh.setStretchLastSection(False)
            hh.setSectionsClickable(True)
            if check_pos is not None:
                hh.resizeSection(check_pos, 5)
                hh.setSectionResizeMode(check_pos, QHeaderView.Fixed)
            hh.setSectionResizeMode(self.__model.name_pos, QHeaderView.Stretch)
            if self.__model.type_pos:
                hh.setSectionResizeMode(self.__model.type_pos, QHeaderView.Stretch)
            self._searchableModel.setFilterKeyColumn(self.__model.name_pos)
            self._searchBar.textChanged.connect(self._searchableModel.setFilterRegExp)
            hh.sectionClicked.connect(self.__model.onHeaderClicked)
            self.tableView.verticalHeader().setDefaultAlignment(Qt.AlignHCenter)


class IncrementalAttributeTableView(QTableView):
    selectedAttributeChanged = Signal(int)

    def __init__(self, namecol: int, period: int = 0, parent: QWidget = None):
        super().__init__(parent)
        self.__timer = QBasicTimer()
        self.__timerPeriodMs = period
        self.__attNameColumn = namecol
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.__filtered = False

    def setModel(self, model: QSortFilterProxyModel, filtered: bool) -> None:
        """ Reimplemented to start fetch timer """
        self.__filtered = filtered
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
        checkable: int = model.sourceModel().sourceModel().checkbox_pos \
            if self.__filtered else model.sourceModel().checkbox_pos
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
            index = self.model().mapToSource(current)
            realRow = index.row() if not self.__filtered else self.model().sourceModel() \
                .mapToSource(index).row()
            self.selectedAttributeChanged.emit(realRow)
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
