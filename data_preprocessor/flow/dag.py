from typing import Any, Dict, List, Optional

import networkx as nx

from data_preprocessor import data, flogging, exceptions as exp
from data_preprocessor.utils import UIdGenerator


class OperationDag:
    """ Provides adding and removing functionality over a NetworkX directed graph intended to store
    nodes of computation. In particular it takes care to update descendants whenever some ancestor node
    is deleted or updated and removes in/out edges when a node is deleted. It also checks if
    connections can be added with respect to the operation settings. """

    def __init__(self, graph: nx.DiGraph = None):
        self.__G = nx.DiGraph() if not graph else graph

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
        :param options: any argument to pass to
            :func:`~data_preprocessor.operation.interface.GraphOperation.setOptions`
        :return True if the options were set, False otherwise
        :raise ValueError: if the node is not in the graph
        """
        if node_id not in self.__G:
            flogging.appLogger.error('Cannot update a node which does not belong to the graph')
            return False
        # Set options for operation
        node: 'OperationNode' = self[node_id]
        node.operation.setOptions(*options, **kwoptions)
        # Update every connected node
        self.__update_descendants(node_id)
        return True

    def addNode(self, node: 'OperationNode') -> bool:
        """ Adds a node to the graph. Must not be already in the graph

        :param node: the node to add
        :return: True if the node was inserted, False if not (e.g. if it was already in the graph)
        """
        if node.uid in self.__G:
            flogging.appLogger.error('Node uid={:d} is already present in the graph'.format(node.uid))
            return False
        self.__G.add_node(node.uid, op=node)
        # self.__update_descendants(node.uid)  # TOCHECK: is it needed?
        return True

    def addConnection(self, source_id: int, target_id: int, slot: int) -> bool:
        """ Add a directed edge between two operations

        :param source_id: id of the source
        :param target_id: id of target
        :param slot: the position of the input passed by the source operation
        :return: True if the connection was added, False otherwise
        :raise DagException: to signal specific errors
        """
        if source_id not in self.__G or target_id not in self.__G:
            flogging.appLogger.error('New edge "{:d}->{:d}" requires non existent node. Add the nodes '
                                     'first'.format(source_id, target_id))
            return False
        target_node: 'OperationNode' = self[target_id]
        source_node: 'OperationNode' = self[source_id]
        from_max_out = source_node.operation.maxOutputNumber()
        to_max_in = target_node.operation.maxInputNumber()
        if (0 <= from_max_out <= self.__G.out_degree(source_id)) or (
                0 <= to_max_in <= self.__G.in_degree(target_id)):
            flogging.appLogger.debug('Edge ({}->{}) not created because of degree constraints'.format(
                source_id, target_id))
            raise exp.DagException(message='Edge "{}->{}" not created because maximum in/out-degree is '
                                           'violated'.format(source_node.operation.name(),
                                                             target_node.operation.name()))

        if not source_node.operation.isOutputShapeKnown() and \
                target_node.operation.needsInputShapeKnown():
            flogging.appLogger.debug('Edge ({}->{}) not created because source node output shape is '
                                     'unknown and target node needs an input shape'
                                     .format(source_id, target_id))
            raise exp.DagException(message='Edge "{}->{}" not created because source operation yields ' \
                                           'undefined output shape and target operation needs it'
                                   .format(source_node.operation.name(), target_node.operation.name()))

        if self.__G.has_edge(source_id, target_id):
            # Avoid connecting the same node twice (debatable)
            flogging.appLogger.debug(
                'Edge ({}->{}) not created because already exists'.format(source_id, target_id))
            raise exp.DagException(message='Edge {}->{} not created it already exists'
                                   .format(source_node.operation.name(), target_node.operation.name()))

        # Add connection
        self.__G.add_edge(source_id, target_id)
        # If the edge forms a cycle do nothing and return False
        if not nx.is_directed_acyclic_graph(self.__G):
            self.__G.remove_edge(source_id, target_id)
            flogging.appLogger.debug(
                'Edge ({}->{}) not created because it creates a cycle'.format(source_id, target_id))
            raise exp.DagException(
                message='Edge "{}->{}" not created because resulting graph is not acyclic'
                    .format(source_node.operation.name(), target_node.operation.name()))

        target_node.setSourceOperationInputPosition(source_id, slot)
        target_node.addInputShape(source_node.operation.getOutputShape(), source_id)

        # Update input shapes in descendants
        self.__update_descendants(target_id)

        flogging.appLogger.debug('Edge ({}->{}) was created'.format(source_id, target_id))
        return True

    def removeConnection(self, source_id: int, target_id: int) -> bool:
        """ Removes a single edge 'source -> target'

        :param source_id: id of the source node
        :param target_id: id of the target node
        :return: True if the edge was removed, False otherwise
        """
        if not self.__G.has_edge(source_id, target_id):
            flogging.appLogger.error('Removing non existent edge ({}->{})'.format(source_id, target_id))
            return False
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
        # Remove all incoming edges
        for u in list(self.__G.predecessors(op_id)):
            self.removeConnection(u, op_id)
        # Remove all outgoing edges
        for v in list(self.__G.successors(op_id)):
            self.removeConnection(op_id, v)
        # Remove node
        self.__G.remove_node(op_id)
        return True

    def __getitem__(self, uid: int) -> 'OperationNode':
        """ Return the operation node with specified id """
        return self.__G.nodes[uid]['op']

    def serialize(self) -> Dict:
        nodes: Dict[int, Dict] = dict()  # {id: node_data}
        for node_id in self.__G.nodes:
            node: OperationNode = self[node_id]
            s = node.serialize()
            nodes[node_id] = s
        edges: List = list()
        for edge in self.__G.edges:
            edges.append(edge)

        serializeDict = dict()
        serializeDict['nodes'] = nodes
        serializeDict['edges'] = edges
        return serializeDict

    @staticmethod
    def deserialize(state: Dict) -> 'OperationDag':
        graph = OperationDag()
        try:
            nodes: Dict[int, Dict] = state['nodes']
            edges: List = state['edges']
            for nodeId, serNode in nodes.items():
                node = OperationNode.deserialize(serNode)
                graph.__G.add_node(nodeId, op=node)

            for edge in edges:
                source_id, target_id = edge
                graph.__G.add_edge(source_id, target_id)
        except (AttributeError, KeyError) as e:
            raise exp.DagException('Error during deserialization', str(e))
        return graph


class OperationNode:
    """ Wraps an operation, providing functionality required for graph computation """

    def __init__(self, operation: 'GraphOperation'):
        self.__op_uid: int = None
        self.operation = None
        # List of inputs, kept in order
        self.__inputs: List = None
        # Input mapper { operation_id: position }
        self.__input_order: Dict[int, int] = dict()
        if operation is not None:
            self.__op_uid = UIdGenerator().getUniqueId()
            self.operation = operation
            # List of inputs, kept in order
            self.__inputs = [None] * operation.maxInputNumber()

    @property
    def inputOrder(self) -> Dict[int, int]:
        return self.__input_order

    @property
    def uid(self) -> int:
        """ Returns the integer unique identifier of one node """
        return self.__op_uid

    def serialize(self) -> Dict:
        d = dict()
        d['type'] = type(self.operation)
        d['shapes'] = [s.serialize() if s else None for s in self.operation.shapes]
        d['options'] = self.operation.getOptions()
        d['order'] = self.__input_order
        d['uid'] = self.uid
        return d

    @staticmethod
    def deserialize(state: Dict) -> 'OperationNode':
        node = OperationNode(None)
        node.operation = state['type']()
        node.operation._shapes = [data.Shape.deserialize(s) if s else None for s in state['shapes']]
        node.__op_uid = state['uid']
        node.__inputs = [None] * node.operation.maxInputNumber()
        node.__input_order = state['order']
        options = state['options']
        try:
            if isinstance(options, dict):
                node.operation.setOptions(**options)
            else:
                node.operation.setOptions(*options)
        except exp.OptionValidationError:
            # If options are not valid it means that the operation was not configured
            # Thus just ignore the configuration (just log a warning)
            flogging.appLogger.warning('An un-configured operation "{}" has been deserialized'.format(
                state['type'].__name__))
        return node

    def inputShapeFrom(self, node_id: int) -> Optional[data.Shape]:
        """ Get the input shape set from specified source node, if set """
        return self.operation.shapes[self.__input_order[node_id]]

    @property
    def nInputs(self) -> int:
        inputs = [i for i in self.__inputs if i is not None]
        return len(inputs)

    @property
    def inputs(self) -> List[data.Frame]:
        return self.__inputs

    def setSourceOperationInputPosition(self, op_id: int, pos: int) -> None:
        """ Call this method to ensure that the output of one parent (source) operation is always passed
        at a specified position when the execute method is called

        :param op_id: the unique id of the operation
        :param pos: the position, which means that input is passed as the argument at position 'pos'
        to 'execute' method. Must be non-negative
        :raise ValueError: if 'pos' is negative
        """
        if pos < 0:
            raise ValueError('Position argument \'pos\' must be non-negative')
        self.__input_order[op_id] = pos

    def unsetSourceOperationInputPosition(self, op_id: int) -> None:
        """ Delete the entry for specified operation in the input mapper

        :param op_id: the unique id of the operation
        """
        del self.__input_order[op_id]

    def addInputArgument(self, arg: Any, op_id: int) -> None:
        """ Add the input argument of an operation to the existing inputs

        :param arg: the input to add
        :param op_id: the unique id of the operation which generated the input. This argument is
            always required
        """
        pos = self.__input_order.get(op_id, None)
        self.__inputs[pos] = arg

    def addInputShape(self, shape: data.Shape, op_id: int) -> None:
        """ Adds the input shape coming from operation with specified id

        :param shape: the shape
        :param op_id: the id of the operation which generated the shape
        """
        pos = self.__input_order.get(op_id, None)
        self.operation.addInputShape(shape, pos)

    def removeInputShape(self, op_id: int) -> None:
        """ Remove the input shape coming from specified operation

        :param op_id: the unique identifier of the operation whose input shape should be removed
        """
        pos = self.__input_order.get(op_id)
        self.operation.removeInputShape(pos)

    def clearInputArgument(self) -> None:
        """ Delete all input arguments cached in a node """
        self.__inputs: List = [None] * self.operation.maxInputNumber()

    def execute(self) -> data.Frame:
        """ Execute the operation with input arguments. Additionally checks that everything is
        correctly set """

        op = self.operation
        inputs = [i for i in self.__inputs if i is not None]

        # Check if input is set
        if op.maxInputNumber() < len(inputs) < op.minInputNumber():
            raise ValueError(
                '{}.execute(input=...), input argument not correctly set'.format(
                    self.__class__.__name__))

        return op.execute(*inputs)
