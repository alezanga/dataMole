import datetime
import logging
import os

from PySide2.QtCore import QtMsgType, QMessageLogContext

LEVEL = logging.DEBUG
LOG_FOLDER = 'logs'
LOG_PATH = ''


def qtMessageHandler(msg_type: QtMsgType, context: QMessageLogContext, msg: str):
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


def setUpLogger() -> None:
    log_path = os.path.join(os.getcwd(), LOG_FOLDER)
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
