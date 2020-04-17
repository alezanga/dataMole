from typing import Union, Any, List, Dict

from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide2.QtWidgets import QWidget

from data_preprocessor.data import Shape


class AttributeTableModel(QAbstractTableModel):
    def __init__(self, parent: QWidget = None, shape: Shape = None, checkable: bool = False,
                 editable: bool = False):
        """ Creates a tablemodel to hold attributes list

        :param parent: parent widget
        :param shape: a Shape object
        :param checkable: whether an additional column with checkbox must be added
        :param editable: whether the model must support attribute renaming
        """
        super().__init__(parent)
        self._shape: Shape = shape
        self._checkable: bool = checkable
        self._editable: bool = editable
        # Keeps track of checked items
        self._checked: List[bool] = ([False] * len(shape.col_names)) if (
                shape and checkable) else list()
        # Keeps track of changes in names for attribute name column
        self._edits: Dict[int, str] = dict()

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

    def checkedAttributes(self) -> List[int]:
        """ Get selected rows if the model is checkable """
        return [i for i, v in enumerate(self._checked) if v] if self._checkable else None

    def editedAttributes(self) -> Dict[int, str]:
        """ Get attributes that were edited, or None if the list is not editable  """
        return self._edits.copy() if self._editable else None

    def setCheckedAttributes(self, c: List[int]) -> None:
        """ Set the checked attributes in the model and update the view """
        if self._checkable:
            self.beginResetModel()
            self._checked = [(a in c) for a in range(0, len(self._checked))]
            self.endResetModel()

    def setEditedAttributes(self, e: (Dict[int, str], Shape)) -> None:
        """ Set the edited attributes in the model and update the view """
        self.beginResetModel()
        self._edits = e[0]
        self._shape = e[1]
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = ...) -> int:
        if parent.isValid():
            return 0
        return len(self._shape.col_names) if self._shape else 0

    def columnCount(self, parent: QModelIndex = ...) -> int:
        if parent.isValid():
            return 0
        return 3 if self._checkable else 2

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if not index.isValid():
            return None

        if index.column() == self._name_pos:
            value = self._shape.col_names[index.row()]
            # Gets updated value or None
            new_val: str = self._edits.get(index.row(), None)
            # If attribute name was edited before
            if new_val:
                if role == Qt.DisplayRole:
                    return value + ' -> ' + new_val
                elif role == Qt.EditRole:
                    return new_val
        elif index.column() == self._type_pos:
            value = self._shape.col_types[index.row()]
        else:
            value = None

        # Return the value to show in the view
        if role == Qt.DisplayRole:
            return value
        # Return the value to show when text is edited
        elif role == Qt.EditRole:
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
        if index.isValid():
            if role == Qt.EditRole and index.column() == self._name_pos and value != index.data(
                    Qt.DisplayRole):
                # TODO: add regex validator
                self._edits[index.row()] = value
            elif role == Qt.CheckStateRole and index.column() == self._checkbox_pos:
                i: int = index.row()
                self._checked[i] = not self._checked[i]
            else:
                return False
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
        flags = Qt.ItemIsEnabled
        if self._editable and index.column() == self._name_pos:
            flags |= Qt.ItemIsEditable
        elif self._checkable and index.column() == self._checkbox_pos:
            flags |= Qt.ItemIsUserCheckable
        return flags
