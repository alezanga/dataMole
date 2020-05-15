from enum import Enum
from typing import Any, List, Union

from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt, Slot, QAbstractItemModel, \
    QSortFilterProxyModel
from PySide2.QtWidgets import QWidget, QTableView, QLineEdit, QVBoxLayout, QHeaderView

from data_preprocessor.data import Frame, Shape
from data_preprocessor.data.types import Types


# New role to return raw data from header
class MyRoles(Enum):
    DataRole = Qt.UserRole


class FrameModel(QAbstractTableModel):
    """ Table model for a single dataframe """

    DataRole = MyRoles.DataRole
    COL_BATCH_SIZE = 50

    def __init__(self, parent: QWidget = None, frame: Frame = Frame(), nrows: int = 10):
        super().__init__(parent)
        self._frame: Frame = frame
        self._shape: Shape = self._frame.shape
        self._n_rows: int = nrows
        self._loadedCols: int = self.COL_BATCH_SIZE

    def setFrame(self, frame: Frame) -> None:
        self.beginResetModel()
        self._frame = frame
        self._shape: Shape = self._frame.shape
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return self._frame.nRows if self._frame.nRows < self._n_rows else self._n_rows

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        allCols = self._frame.shape.n_columns
        if allCols < self._loadedCols:
            return allCols
        return self._loadedCols

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if index.isValid() and index.row() < self._n_rows:
            if role == Qt.DisplayRole:
                return str(self._frame.at((index.row(), index.column())))
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self._shape.col_names[section] + '\n' + self._shape.col_types[section].value
            elif role == FrameModel.DataRole:
                return self._shape.col_names[section], self._shape.col_types[section]
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            if self._shape.has_index():
                return self._frame.index[section]
        return None

    def setHeaderData(self, section: int, orientation: Qt.Orientation, value: Any, role: int = ...) \
            -> bool:
        """ Change column name """
        if orientation == Qt.Horizontal and role == Qt.EditRole and section < self.columnCount():
            names = self._frame.colnames
            names[section] = value
            self._frame = self._frame.rename({self.headerData(section, orientation,
                                                              FrameModel.DataRole)[0]: value})
            self._shape.col_names[section] = value
            self.headerDataChanged.emit(orientation, section, section)
            return True
        return False

    def canFetchMore(self, parent: QModelIndex) -> bool:
        """ Returns True if more columns should be displayed, False otherwise """
        if self._frame.shape.n_columns > self._loadedCols:
            return True
        return False

    def fetchMore(self, parent: QModelIndex):
        remainder = self._frame.shape.n_columns - self._loadedCols
        colsToFetch = min(remainder, self.COL_BATCH_SIZE)
        self.beginInsertColumns(parent, self._loadedCols, self._loadedCols + colsToFetch - 1)
        self._loadedCols += colsToFetch
        self.endInsertColumns()


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
        name: str
        col_type: Types
        name, col_type = self._sourceModel.headerData(index.row(), orientation=Qt.Horizontal,
                                                      role=FrameModel.DataRole)
        value = None
        if index.column() == self.name_pos:
            value = name
        elif index.column() == self.type_pos:
            value = col_type.value

        if role == Qt.DisplayRole or role == Qt.EditRole:
            return value
        # Return the correct value for checkbox
        elif role == Qt.CheckStateRole:
            if index.column() == self.checkbox_pos:
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
        # if self._checkable:
        #     if orientation == Qt.Horizontal and role == Qt.DecorationRole:
        #         if section == self.__checkbox_pos:
        #             return QPixmap(self.header_icon).scaled(100, 100, Qt.KeepAspectRatio,
        #                                                     Qt.SmoothTransformation)

        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == self.name_pos:
                return 'Attribute'
            elif section == self.type_pos:
                return 'Type'

        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags
        flags = Qt.ItemIsEnabled
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
        self._tableView = QTableView(self)
        self._tableModel = QSortFilterProxyModel(self)
        self._tableModel.setSourceModel(self.__model)
        self._tableModel.setFilterCaseSensitivity(Qt.CaseInsensitive)

        self._searchBar = QLineEdit(self)
        self._searchBar.setPlaceholderText('Search')

        layout = QVBoxLayout()
        layout.addWidget(self._searchBar)
        layout.addWidget(self._tableView)
        self.setLayout(layout)

    def setSourceModel(self, source: FrameModel) -> None:
        self.__model.setSourceModel(source)
        if self._tableView.model() is not self._tableModel:
            self._tableView.setModel(self._tableModel)
            hh = self._tableView.horizontalHeader()
            check_pos = self.__model.checkbox_pos
            if check_pos:
                hh.resizeSection(check_pos, 10)
                hh.setSectionResizeMode(check_pos, QHeaderView.Fixed)
            hh.setSectionResizeMode(self.__model.name_pos, QHeaderView.Stretch)
            hh.setSectionResizeMode(self.__model.type_pos, QHeaderView.Fixed)
            hh.setStretchLastSection(False)
            self._tableModel.setFilterKeyColumn(self.__model.name_pos)
            self._tableView.setHorizontalHeader(hh)
            self._searchBar.textChanged.connect(self._tableModel.setFilterRegExp)

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
