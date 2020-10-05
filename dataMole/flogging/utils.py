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

import datetime
import logging
import os

import prettytable as pt
from PySide2.QtCore import QtMsgType, QMessageLogContext

LEVEL = logging.DEBUG
INFO = logging.INFO
LOG_FOLDER = 'logs'
# Contains path of current file log
LOG_PATH = ''
_appLogger = logging.getLogger('app')


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
        _appLogger.debug(msg)
    elif msg_type == QtMsgType.QtCriticalMsg:
        _appLogger.critical(msg)
    elif msg_type == QtMsgType.QtInfoMsg:
        _appLogger.info(msg)
    elif msg_type == QtMsgType.QtWarningMsg:
        _appLogger.warning(msg)
    elif msg_type == QtMsgType.QtFatalMsg:
        _appLogger.fatal(msg)


def setUpRootLogger() -> None:
    """ Sets up a root logger with everything """
    log_path = os.path.join(os.getcwd(), LOG_FOLDER, 'root')
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H.%M.%S.%f')
    global LOG_PATH
    LOG_PATH = os.path.join(log_path, timestamp + '.log')
    logging.basicConfig(filename=LOG_PATH, level=LEVEL,
                        filemode='w',
                        format='%(asctime)s:%(levelname)s:%(module)s.%(funcName)s:%(lineno)d:%('
                               'message)s')
    logging.info('Created log file in {}'.format(LOG_PATH))


def setUpLogger(name: str, folder: str, fmt: str, level: int) -> logging.Logger:
    """
    Creates a logger with specified name, format and level in folder

    :param name: log name
    :param folder: the name of the folder (not path). Path will be "logs/{folder}"
    :param fmt: format as for logging
    :param level: level as for logging
    :return: the created logger
    """
    log_path = os.path.join(os.getcwd(), LOG_FOLDER, folder)
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H.%M.%S.%f')
    log_path = os.path.join(log_path, timestamp + '.log')
    handler = logging.FileHandler(log_path)
    formatter = logging.Formatter(fmt)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.info('Created log file "{}"'.format(name))

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


def deleteOldLogs(keepLastN: int = 5) -> None:
    """ Delete older logs keeping the last N """
    logF = os.path.join(os.getcwd(), LOG_FOLDER)
    subDirs = next(os.walk(logF))[1]
    for subDir in subDirs:
        for path, _, files in os.walk(os.path.join(logF, subDir)):
            ascendingFiles = sorted(files)
            tn = len(ascendingFiles) - keepLastN
            for file in ascendingFiles[:tn]:
                os.remove(os.path.join(path, file))
