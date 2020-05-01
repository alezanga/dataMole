from typing import List

from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget

from .node import NodeSlot, Node
from .scene import Scene
from .view import View
from ...flow import OperationNode
from ...flow.OperationDag import OperationDag
from ...operation import Operation


class GraphController(QWidget):
    def __init__(self, operation_dag: OperationDag, scene: Scene, view: View, parent: QWidget = None):
        super().__init__(parent)
        self._scene: Scene = scene
        self._view: View = view
        self._operation_dag: OperationDag = operation_dag
        # Connections
        self._scene.editModeEnabled.connect(self.editNode)
        self._view.deleteSelected.connect(self.removeItems)
        self._scene.createNewEdge.connect(self.addEdge)

    def addNode(self, op: Operation):
        node = OperationNode(op)
        if self._operation_dag.addNode(node):
            inputs = ['in {}'.format(i) for i in range(op.maxInputNumber())]
            self._scene.create_node(name=op.name(), id=node.uid, inputs=inputs)

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
    def editNode(self, node_id: int):
        node: OperationNode = self._operation_dag[node_id]
        assert node.uid == node_id
        # Show editor
        node.operation.getEditor().show()
        pass
        # Connect editor signals to a slot which calls DAg's update operation
