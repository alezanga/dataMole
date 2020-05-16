import logging
from typing import Any

import networkx as nx

from data_preprocessor.flow import OperationNode


class OperationDag:
    """ Provides adding and removing functionality over a NetworkX directed graph intended to store
    nodes of computation. In particular it takes care to update descendants whenever some ancestor node
    is deleted or updated and removes in/out edges when a node is deleted. It also checks if
    connections can be added with respect to the operation settings. """

    def __init__(self):
        self.__G = nx.DiGraph()

    def getNxGraph(self) -> nx.DiGraph:
        """ Returns a reference to the NetworkX graph """
        return self.__G

    def __update_descendants(self, parent_id: int) -> None:
        """
        Recursively update the descendants of a provided node. Updates the input shape and unset
        options if the input shape changed

        :param parent_id: the id of the parent node
        """
        for child_id in self.__G.successors(parent_id):  # Direct successors
            child_node = self[child_id]
            newParentOutputShape = self[parent_id].operation.getOutputShape()
            oldParentOutputShape = child_node.inputShapeFrom(parent_id)
            if newParentOutputShape != oldParentOutputShape:
                child_node.operation.unsetOptions()
                child_node.addInputShape(newParentOutputShape, parent_id)
                self.__update_descendants(child_id)

    def updateNodeOptions(self, node_id: int, *options: Any, **kwoptions: Any) -> bool:
        """ Set/updates the options of a node.

        :param node_id: the id of the node to update
        :param options, kwoptions: any argument to pass to
            :func:`~data_preprocessor.operation.interface.Operation.setOptions`
        :return True if the options were set, False otherwise
        :raise ValueError: if the node is not in the graph
        """
        if node_id not in self.__G:
            logging.info('Cannot update a node which does not belong to the graph')
            return False
        # Set options for operation
        node: OperationNode = self[node_id]
        node.operation.setOptions(*options, **kwoptions)
        # if node.operation.maxInputNumber() == 0:  # if it's an input op
        #     node.operation.inferInputShape()
        # Update every connected node
        self.__update_descendants(node_id)
        # TOCHECK: else clause should not update since shape is the same
        return True

    def addNode(self, node: OperationNode) -> bool:
        """ Adds a node to the graph. Must not be already in the graph

        :param node: the node to add
        :return: True if the node was inserted, False if not (e.g. if it was already in the graph)
        """
        if node.uid in self.__G:
            return False
        self.__G.add_node(node.uid, op=node)
        # if node.operation.maxInputNumber() == 0:
        # Then it's an input operation and the shape can be inferred
        # in_op: 'InputOperation' = node.operation
        # in_op.inferInputShape()
        # self.__update_descendants(node.uid)  # TOCHECK: is it needed?
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

        if not source_node.operation.isOutputShapeKnown() and \
                target_node.operation.minOutputNumber() != 0:
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
        """ Removes a single edge 'source -> target'

        :param source_id: id of the source node
        :param target_id: id of the target node
        :return: True if the edge was removed, False otherwise
        :raise ValueError: if the edge is nonexistent
        """
        if not self.__G.has_edge(source_id, target_id):
            raise ValueError('Removing non existent edge')
        self.__G.remove_edge(source_id, target_id)
        target_node = self[target_id]
        # Removes source' input shape from target node
        target_node.removeInputShape(source_id)
        # Clean input mapper for target node
        target_node.unsetSourceOperationInputPosition(source_id)
        # Unset options which depends on the input shape
        target_node.operation.unsetOptions()
        # Updates (remove) input shapes (and options) in descendants
        self.__update_descendants(target_id)
        return True

    def removeNode(self, op_id: int) -> bool:
        """ Removes a node from the graph, also all its edges

        :param op_id: the id of the node to remove
        :return: True if the node was removed, False otherwise
        """
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
