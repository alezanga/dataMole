import datetime
import logging
import os

import pandas as pd
from PySide2.QtCore import QtMsgType, QMessageLogContext

LEVEL = logging.DEBUG
LOG_FOLDER = 'logs'
# Contains path of current file log
LOG_PATH = ''


def qtMessageHandler(msg_type: QtMsgType, context: QMessageLogContext, msg: str):
    """ Redirects Qt messages to logging """
    rec = logging.makeLogRecord({
        'lineno': context.line,
        'filename': context.file,
        'funcName': context.function})

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


def dataframeDiffLog(df1, df2) -> str:
    """ Returns a log message with the main differences between the two dataframes

    :param df1: the original Frame
    :param df2: the transformed Frame
    """
    shape1 = df1.shape
    shape2 = df2.shape
    cols1 = set(zip(shape1.colNames, shape1.colTypes))
    cols2 = set(zip(shape2.colNames, shape2.colTypes))
    newCols = cols2 - cols1
    dropCols = cols1 - (cols1 & cols2)
    # Now pretty print them
    newSeries = pd.Series({n: t for (n, t) in newCols})
    newSeries.index.name = 'Column'
    dropSeries = pd.Series({n: t for (n, t) in dropCols})
    dropSeries.index.name = 'Column'
    msg = '\nCHANGES:\nNew columns added: {}\nColumns dropped: {}\n'.format('\n' + str(newSeries) if
                                                                            not newSeries.empty else None,
                                                                            '\n' + str(dropSeries) if
                                                                            not dropSeries.empty else None)
    msg += 'Original number of columns: {:d}\nNew number of columns: {:d}\n'.format(shape1.nColumns,
                                                                                    shape2.nColumns)
    msg += 'Original number of rows: {:d}\nNew number of rows: {:d}'.format(df1.nRows, df2.nRows)
    return msg

# @singleton
# class Logger(QObject):
#     def __init__(self, parent: QObject = None):
#         super().__init__(parent)
#
#         log_path = os.path.join(os.getcwd(), LOG_FOLDER)
#         if not os.path.exists(log_path):
#             os.mkdir(log_path)
#         timestamp = str(datetime.datetime.now()).replace(' ', '_')
#         self._logname = os.path.join(log_path, timestamp + '.log')
#         logging.basicConfig(filename=self._logname, level=LEVEL,
#                             filemode='w',
#                             format='%(asctime)s:%(levelname)s:%(module)s.%(funcName)s:%(lineno)d:%('
#                                    'message)s')
#
#     @property
#     def logName(self) -> str:
#         return self._logname

# @staticmethod
# def info(msg: str):
#     Logger.infoLog.emit(msg)
#     logging.info(msg)
#
# def critical(self, msg: str):
#     self.criticalLog.emit(msg)
#     logging.critical(msg)
#
# def warning(self, msg: str):
#     logging.warning(msg)
#
# def debug(self, msg: str):
#     logging.debug(msg)
#
# def exception(self, msg: str):
#     logging.exception(msg)
