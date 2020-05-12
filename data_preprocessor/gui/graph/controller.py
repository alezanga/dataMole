from typing import List, Callable

from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget, QMessageBox

from data_preprocessor.gui.editor.interface import AbsOperationEditor
from .node import NodeSlot, Node
from .scene import Scene
from .view import View
from ..workbench import WorkbenchModel
from ...flow import OperationNode
from ...flow.OperationDag import OperationDag


class GraphController(QWidget):
    def __init__(self, operation_dag: OperationDag, scene: Scene, view: View,
                 workbench_mod: WorkbenchModel, parent: QWidget = None):
        super().__init__(parent)
        self._scene: Scene = scene
        self._view: View = view
        self._operation_dag: OperationDag = operation_dag
        self._workbench_model: WorkbenchModel = workbench_mod
        # Current active editor
        self.__editor_widget: AbsOperationEditor = None
        # Current node being edited
        self.__editor_node_id: int = None
        # Connections
        self._scene.editModeEnabled.connect(self.startEditNode)
        self._view.deleteSelected.connect(self.removeItems)
        self._scene.createNewEdge.connect(self.addEdge)
        self._scene.dropNewNode.connect(self.addNode)

    @Slot(object)
    def addNode(self, op_class: Callable):
        op_input: bool = getattr(op_class, 'maxInputNumber')() == 0
        op_output: bool = getattr(op_class, 'minOutputNumber')() == 0
        if op_output or op_input:
            op = op_class(self._workbench_model)
        else:
            op = op_class()
        node = OperationNode(op)
        if self._operation_dag.addNode(node):
            inputs = ['in {}'.format(i) for i in range(op.maxInputNumber())]
            self._scene.create_node(name=op.name(), id=node.uid, inputs=inputs, output=not op_output)

    @Slot(NodeSlot, NodeSlot)
    def addEdge(self, source_slot: NodeSlot, target_slot: NodeSlot):
        u: Node = source_slot.parentNode
        v: Node = target_slot.parentNode
        if self._operation_dag.addConnection(source_id=u.id, target_id=v.id, slot=target_slot.position):
            self._scene.create_edge(source_slot, target_slot)
            print('Create')
        else:
            print('No create')

    @Slot()
    def removeItems(self):
        selected_nodes: List[Node] = self._scene.selectedNodes
        selected_edges: List['Edge'] = self._scene.selectedEdges
        for edge in selected_edges:
            self._operation_dag.removeConnection(edge.sourceNode.id, edge.targetNode.id)
        for node in selected_nodes:
            self._operation_dag.removeNode(node.id)
        # Update the scene
        self._scene.delete_selected()

    @Slot(int)
    def startEditNode(self, node_id: int):
        node: OperationNode = self._operation_dag[node_id]
        if not self.__editor_widget:
            if not node.operation.needsOptions():
                msg_noeditor = QMessageBox()
                msg_noeditor.setWindowTitle(node.operation.name())
                msg_noeditor.setInformativeText(
                    'This operations require no options.<hr><b>Operation description</b><br><br>' +
                    node.operation.info())
                msg_noeditor.setStandardButtons(QMessageBox.Ok)
                msg_noeditor.exec_()
                msg_noeditor.deleteLater()
                return
            # Set up editor
            self.__editor_widget = node.operation.getEditor()
            self.__editor_node_id = node.uid
            # Set types
            self.__editor_widget.setTypes(node.operation.acceptedTypes())
            # Set input shapes
            self.__editor_widget.setInputShapes(node.operation._shape)
            # If input/output op set workbench
            if node.operation.maxInputNumber() == 0 or node.operation.minOutputNumber() == 0:
                # Then its an input/output operation
                self.__editor_widget.setWorkbench(node.operation.workbench)
            # Create the central widget and adds options
            self.__editor_widget.setUpEditor()
            self.__editor_widget.setOptions(*node.operation.getOptions())
            # Connect editor signals to slots which handle accept/reject
            self.__editor_widget.acceptAndClose.connect(self.onEditAccept)
            self.__editor_widget.rejectAndClose.connect(self.cleanupEditor)
            # Show the editor in new window
            self.__editor_widget.setParent(None)
            self.__editor_widget.move(self._view.rect().center())
            self.__editor_widget.show()
        else:
            self.__editor_widget.activateWindow()
            self.__editor_widget.raise_()

    @Slot()
    def onEditAccept(self) -> None:
        options = self.__editor_widget.getOptions()
        if self._operation_dag.updateNodeOptions(self.__editor_node_id, *options):
            # Update view
            pass
            print('Edited!')
        else:
            # Signal something in view?
            pass
        # Delete editor
        self.cleanupEditor()

    @Slot()
    def cleanupEditor(self) -> None:
        # Do not call close() here, since this function is called after a closeEvent
        self.__editor_widget.disconnect(self)
        self.__editor_widget.deleteLater()
        self.__editor_node_id = None
        self.__editor_widget = None
