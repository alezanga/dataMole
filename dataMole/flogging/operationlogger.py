# -*- coding: utf-8 -*-
#
# Author:       Alessandro Zangari (alessandro.zangari.code@outlook.com)
# Copyright:    © Copyright 2020 Alessandro Zangari, Università degli Studi di Padova
# License:      GPL-3.0-or-later
# Date:         2020-10-04
# Version:      1.0
#
# This file is part of DataMole.
#
# DataMole is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# DataMole is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with DataMole.  If not, see <https://www.gnu.org/licenses/>.

import logging
from datetime import datetime
from typing import Any, List, Optional

from dataMole import data
from dataMole.flogging.loggable import Loggable
from dataMole.flogging.utils import logDataframeDiff, logDataframeInfo
from dataMole.flow import dag


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
    def _operationHeader(self, operation: 'Operation') -> None:
        # Log name
        self._stringsToLog.append(
            '# {:s} \nTimestamp: {}\n'.format(operation.name(), str(datetime.now())))

    def log(self, operation: 'Operation', result: Any, **kwargs) -> None:
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
