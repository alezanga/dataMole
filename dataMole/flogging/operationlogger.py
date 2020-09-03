import logging
from datetime import datetime
from typing import Any, List, Optional

from dataMole import data
from dataMole.flogging.loggable import Loggable
from dataMole.flogging.utils import logDataframeDiff, logDataframeInfo
from dataMole.flow import dag
from dataMole.operation.interface.operation import Operation


class GraphOperationLogger:
    def __init__(self, logger: logging.Logger):
        self._logHandle: logging.Logger = logger
        self._stringsToLog: List[str] = list()

    def _operationHeader(self, node: dag.OperationNode) -> None:
        # Log name id
        self._stringsToLog.append(
            '# {:s} (ID {:d})\nTimestamp: {}\n'.format(node.operation.name(), node.uid,
                                                       str(datetime.now())))

    def _logOperationStuff(self, operation: Loggable) -> None:
        # The operation may have something to log
        options = operation.logOptions()
        options = options.strip('\n ') if options else options
        execution = operation.logMessage()
        execution = execution.strip('\n ') if execution else execution
        options = ['## OPTIONS', options] if options else ['## OPTIONS: None']
        execution = ['## EXECUTION', execution] if execution else []
        options.extend(execution)
        self._stringsToLog.extend(options)

    def _logNodeStuff(self, node: dag.OperationNode, result: Optional[data.Frame]) -> None:
        if result is not None:
            # Then do some standard logging of result
            if node.nInputs == 1:
                # If the operation transform a single input, then finds out which columns changed
                self._stringsToLog.extend(['## CHANGES', logDataframeDiff(node.inputs[0], result)])
            # In any case print some information of the resulting dataset
            self._stringsToLog.extend(['## RESULT INFO', logDataframeInfo(result)])

    def log(self, node: dag.OperationNode, result: Optional[data.Frame], **kwargs) -> None:
        if not isinstance(node.operation, Loggable):
            return None
        self._operationHeader(node)
        self._logOperationStuff(node.operation)
        self._logNodeStuff(node, result)

        # Finally write in string
        self._logHandle.info('\n'.join(self._stringsToLog) + '\n')
        # Reset list
        self._stringsToLog = list()


class OperationLogger(GraphOperationLogger):
    def _operationHeader(self, operation: Operation) -> None:
        # Log name
        self._stringsToLog.append(
            '# {:s} \nTimestamp: {}\n'.format(operation.name(), str(datetime.now())))

    def log(self, operation: Operation, result: Any, **kwargs) -> None:
        if not isinstance(operation, Loggable):
            return None
        inputName: str = kwargs.get('input', None)
        outputName: str = kwargs.get('output', None)

        self._operationHeader(operation)
        if inputName is not None:
            self._stringsToLog.append('Input name: {}'.format(inputName))
        if outputName is not None:
            self._stringsToLog.append('Output name: {}'.format(outputName))
        self._logOperationStuff(operation)

        # Finally write in log file
        self._logHandle.info('\n'.join(self._stringsToLog) + '\n')
        # Reset list
        self._stringsToLog = list()
