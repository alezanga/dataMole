from PySide2.QtCore import QObject, QModelIndex, Slot, QAbstractItemModel, Qt, QLocale
from PySide2.QtWidgets import QStyledItemDelegate, QWidget, QStyleOptionViewItem

from data_preprocessor.gui.generic.AbsOperationEditor import AbsOperationEditor
from data_preprocessor.operation import Operation
from typing import Any


class OperationDelegate(QStyledItemDelegate):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem,
                     index: QModelIndex) -> QWidget:
        operation: Operation = index.model().data(index)
        editor: AbsOperationEditor = operation.getEditor()
        editor.acceptAndClose.connect(self.commitAndCloseEditor)
        editor.rejectAndClose.connect(self.closeEditor)
        return editor

    @Slot
    def commitAndCloseEditor(self) -> None:
        # TODO: check how I should emit this signal
        self.commitData.emit(self.sender())
        self.closeEditor.emit(self.sender())

    @Slot
    def closeEditor(self) -> None:
        self.closeEditor.emit(self.sender())

    def setEditorData(self, editor: AbsOperationEditor, index: QModelIndex) -> None:
        """
        Sets data to be displayed in the editor widget
        """
        editor.setOptions(index)

    def setModelData(self, editor: AbsOperationEditor, model: QAbstractItemModel,
                     index: QModelIndex) -> None:
        """ Set edited data back to the model when user finished and accepted changes """
        model.setData(index, editor.getOptions(), Qt.EditRole)

    def displayText(self, value: Operation, locale: QLocale) -> str:
        """ Textual representation of an Operation to show in a Pipeline """
        return value.name()
