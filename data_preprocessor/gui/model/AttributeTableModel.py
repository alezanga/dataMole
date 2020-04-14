from typing import Union, Any, List
from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide2.QtWidgets import QWidget

from data_preprocessor.data import Shape


class AttributeTableModel(QAbstractTableModel):
    def __init__(self, parent: QWidget = None, shape: Shape = None, checkable: bool = False):
        super().__init__(parent)
        self.__shape: Shape = shape
        self.__checkable: bool = checkable
        self.__checked: List[bool] = ([False] * len(shape.col_names)) if shape else list()

    @property
    def checkbox_pos(self) -> Union[int, None]:
        """
        Return the column index for checkbox
        """
        if self.__checkable:
            return 0
        else:
            return None

    @property
    def type_pos(self) -> int:
        """
        Return the column index for type
        """
        if self.__checkable:
            return 1
        else:
            return 0

    @property
    def name_pos(self) -> int:
        """
        Return the column index for name
        """
        if self.__checkable:
            return 2
        else:
            return 1

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.__shape.col_names) if self.__shape else 0

    def columnCount(self, parent: QModelIndex = ...) -> int:
        return 3 if self.__checkable else 2

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if not index.isValid():
            return None

        if index.column() == self.name_pos:
            value = self.__shape.col_names[index.row()]
        elif index.column() == self.type_pos:
            value = self.__shape.col_types[index.row()]
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
            if index.column() == self.checkbox_pos:
                if self.__checked[index.row()]:
                    return Qt.Checked
                else:
                    return Qt.Unchecked
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        return None

    def setData(self, index: QModelIndex, value: Any, role: int = ...) -> bool:
        # TODO
        pass

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        # if self.__checkable:
        #     if orientation == Qt.Horizontal and role == Qt.DecorationRole:
        #         if section == self.__checkbox_pos:
        #             return QPixmap(self.header_icon).scaled(100, 100, Qt.KeepAspectRatio,
        #                                                     Qt.SmoothTransformation)

        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == self.__name_pos:
                return 'Attribute'
            elif section == self.__type_pos:
                return 'Type'

        return None
