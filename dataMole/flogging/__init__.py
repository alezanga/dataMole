"""
Collection of logging utilities
"""

from dataMole.flogging.loggable import Loggable
from dataMole.flogging.operationlogger import GraphOperationLogger, OperationLogger
from dataMole.flogging.utils import *

# Expose all loggers for fast retrieval
graphLogger = logging.getLogger('graph')
opsLogger = logging.getLogger('ops')
appLogger = logging.getLogger('app')
rootLogger = logging.getLogger()
