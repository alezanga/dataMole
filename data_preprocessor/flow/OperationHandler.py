import logging
from datetime import datetime
from typing import Tuple, List

import networkx as nx
from PySide2.QtCore import QThreadPool, Slot, QObject, Signal, Qt

from data_preprocessor import data, logger
from data_preprocessor.flow.OperationDag import OperationDag, OperationNode
from data_preprocessor.logger import dataframeDiffLog
from data_preprocessor.operation.interface.executionlog import OperationLog
from data_preprocessor.status import NodeStatus
from data_preprocessor.threads import Worker


# NOTE: Eventualmente memorizzare con joblib
# from joblib import Memory

class OperationHandler:
    """ Executes a DAG """

    def __init__(self, graph: OperationDag):
        self.graph: nx.DiGraph = graph.getNxGraph()
        self.__qtSlots = _HandlerSlots(self)
        self.signals = HandlerSignals()
        self.toExecute = set()

        # self.__memoryContext = Memory(cachedir='/tmp', verbose=1)

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
        logger.setUpGraphLogger()
        logging.getLogger('graph').info('OPERATION LOG')
        logging.getLogger('graph').info('Execution time: {}\n'.format(datetime.now()))

        for node in input_nodes:
            self.startNode(node)

    def startNode(self, node: OperationNode):
        worker = Worker(node, identifier=node.uid)
        # Connect
        worker.signals.result.connect(self.__qtSlots.nodeCompleted, Qt.QueuedConnection)
        worker.signals.error.connect(self.__qtSlots.nodeErrored, Qt.QueuedConnection)
        self.signals.statusChanged.emit(node.uid, NodeStatus.PROGRESS)
        QThreadPool.globalInstance().start(worker)

    def _canExecute(self, input_nodes: List[OperationNode]) -> bool:
        """
        Check if there are input nodes and if options are set. Additionally sets the set of nodes to
        be executed in field 'toExecute'

        :raise HandlerException if the flow is not ready for execution
        """
        if not input_nodes:
            logging.error('Flow not started: there are no input operations')
            raise HandlerException('There are no input nodes')
        # Find the set of reachable nodes from the input operations
        reachable = set()
        for node in input_nodes:
            reachable = reachable.union(nx.dag.descendants(self.graph, node.uid))
        # Check if all reachable nodes have options set
        for node_id in reachable:
            node: OperationNode = self.graph.nodes[node_id]['op']
            if not node.operation.hasOptions():
                logging.error('Flow not started: operation {}-{} has options to set'.format(
                    node.operation.name(), node.uid))
                raise HandlerException(
                    'GraphOperation {} has options to set'.format(node.operation.name()))
        self.toExecute = reachable | set(map(lambda x: x.uid, input_nodes))
        return True


class HandlerSignals(QObject):
    """
    Graph handler Qt signals.

    - statusChnaged(int, status): operation status changed with new status
    - allFinished: flow execution finished (either because of error or completion)
    """
    statusChanged = Signal(int, NodeStatus)
    allFinished = Signal()


class _HandlerSlots(QObject):
    def __init__(self, handler: OperationHandler, parent: QObject = None):
        super().__init__(parent)
        self.handler = handler

    @Slot(object, object)
    def nodeCompleted(self, node_id: int, result: data.Frame):
        logging.debug('nodeCompleted SUCCESS')
        # Emit node finished
        self.handler.signals.statusChanged.emit(node_id, NodeStatus.SUCCESS)
        # Clear eventual input, since now I have result
        node = self.handler.graph.nodes[node_id]['op']
        # LOG OPERATION
        logEntry = ''
        # Log name id
        logEntry += '####### {:s} (ID {:d})\nTimestamp: {}\n'.format(node.operation.name(),
                                                                     node.uid, str(datetime.now()))
        if isinstance(node.operation, OperationLog):
            # The operation has something to log
            logEntry += node.operation.logMessage().rstrip('\n')
        if node.nInputs == 1 and result is not None:
            # If the operation transform a single input, then finds out which columns changed
            logEntry += dataframeDiffLog(node.inputs[0], result)
        logging.getLogger('graph').info(logEntry + '\n')
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
            child: OperationNode = self.handler.graph.nodes[child_id]['op']
            child.addInputArgument(result, op_id=node_id)
            # Check if child has all it needs to start
            if self.handler.graph.in_degree(child_id) == child.nInputs:
                # If so, add the worker to thread pool
                self.handler.startNode(child)

    @Slot(object, tuple)
    def nodeErrored(self, node_id: int, error: Tuple[type, Exception, str]):
        msg = str(error[1])
        node = self.handler.graph.nodes[node_id]['op']
        node.clearInputArgument()
        logging.error('GraphOperation {} failed with exception {}: {} - trace: {}'.format(
            node.operation.name(), str(error[0]), msg, error[2]))
        self.handler.signals.statusChanged.emit(node_id, NodeStatus.ERROR)


class HandlerException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)
