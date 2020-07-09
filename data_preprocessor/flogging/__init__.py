from data_preprocessor.flogging.loggable import Loggable
from data_preprocessor.flogging.operationlogger import GraphOperationLogger, OperationLogger
from data_preprocessor.flogging.utils import *

# Expose all loggers for fast retrieval
graphLogger = logging.getLogger('graph')
opsLogger = logging.getLogger('ops')
appLogger = logging.getLogger('app')
rootLogger = logging.getLogger()
