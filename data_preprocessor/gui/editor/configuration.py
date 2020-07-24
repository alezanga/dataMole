from PySide2.QtCore import Qt
from PySide2.QtWidgets import QWidget

from data_preprocessor.gui.editor import AbsOperationEditor
from data_preprocessor.operation.interface.operation import Operation


def configureEditor(editor: AbsOperationEditor, op: Operation, parent: QWidget = None):
    """ Configure an editor with standard fields and window size """
    editor.setUpEditor()
    # Configure standard fields
    editor.setWindowTitle(op.name())
    editor.setDescription(op.shortDescription(), op.longDescription())
    editor.acceptedTypes = op.acceptedTypes()
    editor.workbench = op.workbench
    editor.inputShapes = op.shapes if hasattr(op, 'shapes') else list()
    # Set parent and flags
    editor.setParent(parent)
    editor.setWindowFlags(Qt.Window)
    editor.setWindowModality(Qt.ApplicationModal)


def configureEditorOptions(editor: AbsOperationEditor, op: Operation):
    """ Adds options to the editor """
    # Set options
    options = op.getOptions()
    if isinstance(options, dict):
        editor.setOptions(**options)
    else:
        editor.setOptions(*options)
