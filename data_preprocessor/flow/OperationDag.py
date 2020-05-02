from typing import Any

import networkx as nx

from data_preprocessor.flow import OperationNode


class OperationDag:
    def __init__(self):
        self.__G = nx.DiGraph()

    def getNxGraph(self) -> nx.DiGraph:
        """ Returns a reference to the networkx graph """
        return self.__G

    def __update_descendants(self, parent_id: int, unset_options: bool = False) -> None:
        # TOCHECK
        for child_id in self.__G.successors(parent_id):  # Direct successors
            child_node = self[child_id]
            if unset_options:
                child_node.operation.unsetOptions()
            child_node.addInputShape(self[parent_id].operation.getOutputShape(), parent_id)
            self.__update_descendants(child_id)

    def updateNodeOptions(self, node_id: int, *options: Any, **kwoptions: Any) -> bool:
        if node_id not in self.__G:
            raise ValueError('Cannot update a node which does not belong to the graph')
        # Set options for operation
        node: OperationNode = self[node_id]
        node.operation.setOptions(*options, **kwoptions)
        if node.operation.maxInputNumber() == 0:  # if it's an input op
            node.operation.inferInputShape()
        # Update every connected node
        self.__update_descendants(node_id)
        return True

    def addNode(self, node: OperationNode) -> bool:
        if node.uid in self.__G:
            return False
        self.__G.add_node(node.uid, op=node)
        if node.operation.maxInputNumber() == 0 and not node.operation.needsOptions():
            # Then it's an input operation and the shape can be inferred
            in_op: 'InputOperation' = node.operation
            in_op.inferInputShape()
            self.__update_descendants(node.uid)
        return True

    def addConnection(self, source_id: int, target_id: int, slot: int) -> bool:
        """ Add a directed edge between two operations

        :param source_id: id of the source
        :param target_id: id of target
        :param slot: the position of the input passed by the source operation
        :return: True if the connection was added, False otherwise
        """
        if source_id not in self.__G or target_id not in self.__G:
            raise ValueError('New edge requires non existent node. Add the nodes first')
        target_node: OperationNode = self[target_id]
        source_node: OperationNode = self[source_id]
        from_max_out = source_node.operation.maxOutputNumber()
        to_max_in = target_node.operation.maxInputNumber()
        if (0 <= from_max_out <= self.__G.out_degree(source_id)) or (
                0 <= to_max_in <= self.__G.in_degree(target_id)):
            return False

        # Add connection
        self.__G.add_edge(source_id, target_id)
        # If the edge forms a cycle do nothing and return False
        if not nx.is_directed_acyclic_graph(self.__G):
            self.__G.remove_edge(source_id, target_id)
            return False

        target_node.setSourceOperationInputPosition(source_id, slot)
        target_node.addInputShape(source_node.operation.getOutputShape(), source_id)

        # Update input shapes in descendants
        self.__update_descendants(target_id)
        return True

    def removeConnection(self, source_id: int, target_id: int) -> bool:
        if not self.__G.has_edge(source_id, target_id):
            raise ValueError('Removing non existent edge')
        self.__G.remove_edge(source_id, target_id)
        target_node = self[target_id]
        target_node.removeInputShape(source_id)
        target_node.unsetSourceOperationInputPosition(source_id)
        # TOCHECK
        # Unset options which depends on the input shape
        target_node.operation.unsetOptions()
        # Updates (remove) input shapes (and options) in descendants
        self.__update_descendants(target_id, unset_options=True)
        return True

    def removeNode(self, op_id: int) -> bool:
        # TOCHECK
        # Remove all incoming edges
        for u in list(self.__G.predecessors(op_id)):
            self.removeConnection(u, op_id)
        # Remove all outgoing edges
        for v in list(self.__G.successors(op_id)):
            self.removeConnection(op_id, v)
        # Remove node
        self.__G.remove_node(op_id)
        return True

    def __getitem__(self, uid: int) -> OperationNode:
        """ Return the operation node with specified id """
        return self.__G.nodes[uid]['op']
