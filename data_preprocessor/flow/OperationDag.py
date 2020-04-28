from typing import Any

import networkx as nx

from data_preprocessor.flow import OperationNode
from data_preprocessor.operation import InputOperation


class OperationDag:
    def __init__(self):
        self.__G = nx.DiGraph()

    def getNxGraph(self) -> nx.DiGraph:
        """ Returns a reference to the networkx graph """
        return self.__G

    def __update_descendants(self, parent, unset_options: bool = False) -> None:
        # TOCHECK
        for child in self.__G.successors(parent):
            if unset_options:
                child.operation.unsetOptions()
            child.addInputShape(parent.operation.getOutputShape(), parent.uid)
            self.__update_descendants(child)

    def updateNodeOptions(self, node: OperationNode, *options: Any, **kwoptions: Any) -> None:
        if node not in self.__G:
            raise ValueError('Cannot update a node which does not belong to the graph')
        # Set options for operation
        node.operation.setOptions(*options, **kwoptions)
        if node.operation.maxInputNumber() == 0:  # if it's an input op
            node.operation.setInputShape()
        # Update every connected node
        self.__update_descendants(node)

    def addNode(self, node: OperationNode):
        self.__G.add_node(node)
        if node.operation.maxInputNumber() == 0 and not node.operation.needsOptions():
            # Then it's an input operation and the shape can be
            in_op: InputOperation = node.operation
            in_op.inferInputShape()
            self.__update_descendants(node)

    def addConnection(self, _from: OperationNode, _to: OperationNode, slot: int) -> bool:
        if _from not in self.__G or _to not in self.__G:
            raise ValueError('New edge requires non existent node. Add the nodes first')
        from_max_out = _from.operation.maxOutputNumber()
        to_max_in = _to.operation.maxInputNumber()
        if (0 <= from_max_out <= self.__G.out_degree(_from)) or (
                0 <= to_max_in <= self.__G.in_degree(_to)):
            return False

        # Add connection
        self.__G.add_edge(_from, _to)
        # If the edge forms a cycle do nothing and return False
        if not nx.is_directed_acyclic_graph(self.__G):
            self.__G.remove_edge(_from, _to)
            return False

        _to.setOperationInputPosition(_from.uid, slot)
        _to.addInputShape(_from.operation.getOutputShape(), _from.uid)

        # Update input shapes in descendants
        self.__update_descendants(_to)

        return True

    def removeConnection(self, _from: OperationNode, _to: OperationNode) -> bool:
        if not self.__G.has_edge(_from, _to):
            raise ValueError('Removing non existent edge')
        self.__G.remove_edge(_from, _to)
        _to.removeInputShape(_to.uid)
        # TOCHECK
        # Unset options which depends on the input shape
        _to.operation.unsetOptions()
        # Updates (remove) input shapes (and options) in descendants
        self.__update_descendants(_to, unset_options=True)

        return True

    def removeNode(self, op: OperationNode):
        # Remove all joined edges
        for u, v in list(self.__G.degree(op)):
            self.removeConnection(u, v)

        # Remove node
        self.__G.remove_node(op)
