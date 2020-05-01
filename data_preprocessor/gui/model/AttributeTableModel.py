from typing import Union, Any, List

from PySide2.QtCore import QModelIndex, Qt, QAbstractItemModel, Slot, QAbstractTableModel
from PySide2.QtWidgets import QWidget

from data_preprocessor.gui.model.FrameModel import FrameModel


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
    def _checkbox_pos(self) -> Union[int, None]:
        """
        Return the column index for checkbox
        """
        if self._checkable:
            return 0
        else:
            return None

    @property
    def _type_pos(self) -> int:
        """ Return the column index for type """
        if self._checkable:
            return 2
        else:
            return 1

    @property
    def _name_pos(self) -> int:
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
            self.dataChanged.emit(self.index(sec1, self._name_pos),
                                  self.index(sec2, self._name_pos))

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

        name, col_type = self._sourceModel.headerData(index.row(), orientation=Qt.Horizontal,
                                                      role=FrameModel.DataRole)
        value = None
        if index.column() == self._name_pos:
            value = name
        elif index.column() == self._type_pos:
            value = col_type

        if role == Qt.DisplayRole or role == Qt.EditRole:
            return value
        # Return the correct value for checkbox
        elif role == Qt.CheckStateRole:
            if index.column() == self._checkbox_pos:
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
        if role == Qt.EditRole and index.column() == self._name_pos and value != index.data(
                Qt.DisplayRole):
            return self._sourceModel.setHeaderData(index.row(), Qt.Horizontal, value, Qt.EditRole)
        # Toggle checkbox state
        elif role == Qt.CheckStateRole and index.column() == self._checkbox_pos:
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
            if section == self._name_pos:
                return 'Attribute'
            elif section == self._type_pos:
                return 'Type'

        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags
        flags = Qt.ItemIsEnabled
        if self._editable and index.column() == self._name_pos:
            flags |= Qt.ItemIsEditable
        elif self._checkable and index.column() == self._checkbox_pos:
            flags |= Qt.ItemIsUserCheckable
        return flags
