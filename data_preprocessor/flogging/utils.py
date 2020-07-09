import datetime
import logging
import os

import prettytable as pt
from PySide2.QtCore import QtMsgType, QMessageLogContext

LEVEL = logging.DEBUG
LOG_FOLDER = 'logs'
# Contains path of current file log
LOG_PATH = ''


# def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None):
#     """
#     A factory method which can be overridden in subclasses to create
#     specialized LogRecords.
#     """
#     rv = logging.LogRecord(name, level, fn, lno, msg, args, exc_info, func)
#     if extra is not None:
#         rv.__dict__.update(extra)
#     return rv
#
#
# def overrideLogArgs(logger, level=logging.DEBUG, cache=dict()):
#     """Decorator to log arguments passed to func."""
#     arg_log_fmt = '{name}({arg_str})'
#     logger_class = logger.__class__
#     if logger_class in cache:
#         UpdateableLogger = cache[logger_class]
#     else:
#         cache[logger_class] = UpdateableLogger = type(
#             'UpdateableLogger', (logger_class,), dict(makeRecord=makeRecord))
#
#     def inner_func(func):
#         line_no = inspect.getsourcelines(func)[-1]
#
#         @wraps(func)
#         def return_func(*args, **kwargs):
#             arg_list = list('{!r}'.format(arg) for arg in args)
#             arg_list.extend('{}={!r}'.format(key, val) for key, val in kwargs.items())
#             msg = arg_log_fmt.format(name=func.__name__, arg_str=", ".join(arg_list))
#             logger.__class__ = UpdateableLogger
#             try:
#                 logger.log(level, msg, extra=dict(lineno=line_no))
#             finally:
#                 logger.__class__ = logger_class
#             return func(*args, **kwargs)
#
#         return return_func
#
#     return inner_func


def qtMessageHandler(msg_type: QtMsgType, context: QMessageLogContext, msg: str):
    """ Redirects Qt messages to logging """
    rec = {
        'lineno': context.line,
        'filename': context.file,
        'funcName': context.function}

    if msg_type == QtMsgType.QtDebugMsg:
        logging.debug(msg)
    elif msg_type == QtMsgType.QtCriticalMsg:
        logging.critical(msg)
    elif msg_type == QtMsgType.QtInfoMsg:
        logging.info(msg)
    elif msg_type == QtMsgType.QtWarningMsg:
        logging.warning(msg)
    elif msg_type == QtMsgType.QtFatalMsg:
        logging.fatal(msg)


def setUpGraphLogger():
    """ Set up a new log file in folder logs/graph to log every execution of a computational graph """
    log_path = os.path.join(os.getcwd(), LOG_FOLDER, 'graph')
    if not os.path.exists(log_path):
        os.mkdir(log_path)
    timestamp = str(datetime.datetime.now()).replace(' ', '_')
    log_path = os.path.join(log_path, timestamp + '.log')
    handler = logging.FileHandler(log_path)
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger('graph')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger


def setUpAppLogger() -> None:
    """ Sets up a root logger with everything """
    log_path = os.path.join(os.getcwd(), LOG_FOLDER, 'app')
    if not os.path.exists(log_path):
        os.mkdir(log_path)
    timestamp = str(datetime.datetime.now()).replace(' ', '_')
    global LOG_PATH
    LOG_PATH = os.path.join(log_path, timestamp + '.log')
    logging.basicConfig(filename=LOG_PATH, level=LEVEL,
                        filemode='w',
                        format='%(asctime)s:%(levelname)s:%(module)s.%(funcName)s:%(lineno)d:%('
                               'message)s')
    logging.info('Created log file in {}'.format(LOG_PATH))


def setUpOperationLogger() -> logging.Logger:
    log_path = os.path.join(os.getcwd(), LOG_FOLDER, 'operations')
    if not os.path.exists(log_path):
        os.mkdir(log_path)
    timestamp = str(datetime.datetime.now()).replace(' ', '_')
    log_path = os.path.join(log_path, timestamp + '.log')
    handler = logging.FileHandler(log_path)
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger('ops')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger


def logDataframeDiff(df1, df2) -> str:
    """ Returns a log message with the main differences between the two dataframes

    :param df1: the original Frame
    :param df2: the transformed Frame
    """

    def diffNames(new: set, dropped: set, table: pt.PrettyTable):
        while new or dropped:
            removed: tuple = dropped.pop() if dropped else None
            added: tuple = new.pop() if new else None
            strAdded: str = '{} ({})'.format(added[0], added[1].name) if added else ''
            strRemoved: str = '{} ({})'.format(removed[0], removed[1].name) if removed else ''
            table.add_row([strAdded, strRemoved])

    # Diff column names / types
    shape1 = df1.shape
    shape2 = df2.shape
    cols1 = set(zip(shape1.colNames, shape1.colTypes))
    cols2 = set(zip(shape2.colNames, shape2.colTypes))
    newCols = cols2 - cols1
    dropCols = cols1 - (cols1 & cols2)
    # Now pretty print them
    colDiffTable = pt.PrettyTable(field_names=['Columns added', 'Columns removed'], print_empty=False)
    diffNames(newCols, dropCols, colDiffTable)

    # Diff indexes
    index1 = set(zip(shape1.index, shape1.indexTypes))
    index2 = set(zip(shape2.index, shape2.indexTypes))
    newCols = index2 - index1
    dropCols = index1 - (index1 & index2)
    # Now pretty print them
    indexDiffTable = pt.PrettyTable(field_names=['Levels added', 'Levels removed'], print_empty=False)
    diffNames(newCols, dropCols, indexDiffTable)

    cc = colDiffTable.get_string(border=True, vrules=pt.ALL).strip()
    ii = indexDiffTable.get_string(border=True, vrules=pt.ALL).strip()
    msgC = 'Column changes:' + (('\n' + cc) if cc else 'None')
    msgI = '\nIndex changes:' + (('\n' + ii) if ii else 'None')
    return msgC + msgI


def logDataframeInfo(df) -> str:
    shape = df.shape
    tt = pt.PrettyTable(field_names=['N Rows', 'N Columns', 'Index levels', 'Index names'])
    tt.add_row([df.nRows,
                df.nColumns,
                shape.nIndexLevels,
                '\n'.join('{} ({})'.format(k, t.name) for k, t in shape.indexDict.items())])
    return tt.get_string(border=True, vrules=pt.ALL).strip()