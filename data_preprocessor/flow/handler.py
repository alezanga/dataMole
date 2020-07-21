from datetime import datetime
from typing import Tuple, List, Set

import networkx as nx
from PySide2.QtCore import QThreadPool, Slot, QObject, Signal, Qt

from data_preprocessor import data, exceptions as exp
from data_preprocessor import flogging
from data_preprocessor.status import NodeStatus
from data_preprocessor.threads import Worker
from . import dag


class OperationHandler:
    """ Executes a DAG """

    def __init__(self, graph: 'dag.OperationDag'):
        self.graph: nx.DiGraph = graph.getNxGraph()
        self.__qtSlots = _HandlerSlots(self)
        self.signals = HandlerSignals()
        self.toExecute: Set[int] = set()
        self.graphLogger: flogging.GraphOperationLogger = None

    def execute(self):
        """
        Executes the dag flow. This method will emit signals in 'HandlerSignals'

        :raise HandlerException if the flow is not ready to start
        """
        # Find input nodes
        start_nodes_id = [n for (n, deg) in self.graph.in_degree() if deg == 0]
        input_nodes = [node for node in map(lambda nid: self.graph.nodes[nid]['op'], start_nodes_id) if
                       node.operation.maxInputNumber() == 0]
        self._canExecute(input_nodes)

        # Create a logger for the execution
        logger = flogging.setUpLogger(name='graph', folder='graph', fmt='%(message)s',
                                      level=flogging.INFO)
        logger.info('OPERATION LOG')
        logger.info('Execution time: {}\n'.format(datetime.now()))
        self.graphLogger = flogging.GraphOperationLogger(logger)
        # Start execution of all input nodes
        for node in input_nodes:
            self.startNode(node)

    def startNode(self, node: 'OperationNode'):
        worker = Worker(node, identifier=node.uid)
        # Connect
        worker.signals.result.connect(self.__qtSlots.nodeCompleted, Qt.AutoConnection)
        worker.signals.error.connect(self.__qtSlots.nodeErrored, Qt.AutoConnection)
        self.signals.statusChanged.emit(node.uid, NodeStatus.PROGRESS)
        QThreadPool.globalInstance().start(worker)

    def _canExecute(self, input_nodes: List['OperationNode']) -> bool:
        """
        Check if there are input nodes and if options are set. Additionally sets the set of nodes to
        be executed in field 'toExecute'

        :raise HandlerException if the flow is not ready for execution
        """
        if not input_nodes:
            flogging.appLogger.error('Flow not started: there are no input operations')
            raise exp.HandlerException('Flow not started', 'There are no input nodes')
        # Find the set of reachable nodes from the input operations
        reachable = set()
        for node in input_nodes:
            # Also check that input nodes have options set, or raise error
            if not node.operation.hasOptions():
                flogging.appLogger.error(
                    'Flow not started: input operation "{}-{}" is not configured'.format(
                        node.operation.name(), node.uid))
                raise exp.HandlerException('Flow not started',
                                           'Input operation "{}" has options to set'.format(
                                               node.operation.name()))
            # All descendants of input node are reachable
            reachable = reachable.union(nx.dag.descendants(self.graph, node.uid))
        # Check if all reachable nodes have options set
        for node_id in reachable:
            node: 'OperationNode' = self.graph.nodes[node_id]['op']
            if not node.operation.hasOptions():
                flogging.appLogger.error('Flow not started: operation "{}-{}" has options to set'.format(
                    node.operation.name(), node.uid))
                raise exp.HandlerException('Flow not started',
                                           'Operation "{}" has options to set'.format(
                                               node.operation.name()))
        self.toExecute = reachable | set(map(lambda x: x.uid, input_nodes))
        return True


class HandlerSignals(QObject):
    """
    Graph handler Qt signals.

    - statusChnaged(int, status): operation status changed with new status
    - failedWithMessage(int, message): pass an error message
    - allFinished: flow execution finished (either because of error or completion)
    """
    statusChanged = Signal(int, NodeStatus)
    failedWithMessage = Signal(int, str)
    allFinished = Signal()


class _HandlerSlots(QObject):
    def __init__(self, handler: OperationHandler, parent: QObject = None):
        super().__init__(parent)
        self.handler: OperationHandler = handler

    @Slot(object, object)
    def nodeCompleted(self, node_id: int, result: data.Frame):
        flogging.appLogger.debug('nodeCompleted SUCCESS')
        # Emit node finished
        self.handler.signals.statusChanged.emit(node_id, NodeStatus.SUCCESS)
        # Clear eventual input, since now I have result
        node = self.handler.graph.nodes[node_id]['op']
        # Log operation
        self.handler.graphLogger.log(node, result)
        # Delete inputs
        node.clearInputArgument()
        # Remove from task list
        self.handler.toExecute.remove(node_id)
        # Check if it was the last one
        if not len(self.handler.toExecute):
            # All tasks were completed
            self.handler.signals.allFinished.emit()
            return
        # Put result in all child nodes
        for child_id in self.handler.graph.successors(node_id):
            child: 'OperationNode' = self.handler.graph.nodes[child_id]['op']
            child.addInputArgument(result, op_id=node_id)
            # Check if child has all it needs to start
            if self.handler.graph.in_degree(child_id) == child.nInputs:
                # If so, add the worker to thread pool
                self.handler.startNode(child)

    @Slot(object, tuple)
    def nodeErrored(self, node_id: int, error: Tuple[type, Exception, str]):
        self.handler.signals.statusChanged.emit(node_id, NodeStatus.ERROR)
        msg = str(error[1])
        eName = error[0].__name__
        self.handler.toExecute.remove(node_id)
        node = self.handler.graph.nodes[node_id]['op']
        node.clearInputArgument()
        flogging.appLogger.error('GraphOperation {} failed with exception {}: {} - trace: {}'.format(
            node.operation.name(), eName, msg, error[2]))
        self.handler.signals.failedWithMessage.emit(node_id, 'Exception "{}" in "{}": {}'
                                                    .format(eName, node.operation.name(), msg))
        # Log operation
        self.handler.graphLogger.log(node, None)
        # Clear input set in successors and reset execution queue (set)
        for uid in self.handler.toExecute:
            node = self.handler.graph.nodes[uid]['op']
            node.clearInputArgument()
        self.handler.toExecute = set()
        # Emit finished signal
        self.handler.signals.allFinished.emit()
