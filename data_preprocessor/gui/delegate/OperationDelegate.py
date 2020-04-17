from PySide2.QtCore import QObject, QModelIndex, Slot, QAbstractItemModel, Qt, QLocale, QEvent
from PySide2.QtWidgets import QStyledItemDelegate, QWidget, QStyleOptionViewItem

from data_preprocessor.gui.generic.AbsOperationEditor import AbsOperationEditor
from data_preprocessor.operation import Operation


class OperationDelegate(QStyledItemDelegate):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self.__editor_id: str = ''

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem,
                     index: QModelIndex) -> QWidget:
        operation: Operation = index.data(Qt.DisplayRole)
        editor: AbsOperationEditor = operation.getEditor()
        # Save an identifier for the editor in use to be used in eventFilter
        self.__editor_id = editor.id
        editor.acceptAndClose.connect(lambda: self.commitAndCloseEditor(editor))
        editor.rejectAndClose.connect(lambda: self.closeEditorSlot(editor))
        return editor

    @Slot(QWidget)
    def commitAndCloseEditor(self, editor: QWidget) -> None:
        # TODO: check how I should emit this signal
        self.commitData.emit(editor)
        self.closeEditor.emit(editor, QStyledItemDelegate.NoHint)

    @Slot(QWidget)
    def closeEditorSlot(self, editor: QWidget) -> None:
        self.closeEditor.emit(editor, QStyledItemDelegate.NoHint)

    def setEditorData(self, editor: AbsOperationEditor, index: QModelIndex) -> None:
        """
        Sets data to be displayed in the editor widget
        """
        if not index.isValid():
            return None
        if index.column() == 0:
            editor.setOptions(index.data().getOptions())

    def setModelData(self, editor: AbsOperationEditor, model: QAbstractItemModel,
                     index: QModelIndex) -> None:
        """ Set edited data back to the model when user finished and accepted changes """
        model.setData(index, editor.getOptions(), Qt.EditRole)

    def displayText(self, value: Operation, locale: QLocale) -> str:
        """ Textual representation of an Operation to show in a Pipeline """
        return value.name()

    def eventFilter(self, editor: AbsOperationEditor, event: QEvent) -> bool:
        """ Ensure that no event is processed other than one on the editor object """
        if editor.id != self.__editor_id:
            # Return True to filter out events
            return True
        return False
