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

import sys

from PySide2 import QtCore
from PySide2.QtCore import QFile
from PySide2.QtWidgets import QApplication

from dataMole import flogging
# noinspection PyUnresolvedReferences
from dataMole import qt_resources

if __name__ == '__main__':
    print('dataMole v. 0.1')
    print('Built on Python', sys.version)
    # Set up logger, QApp
    app = QApplication([])
    flogging.setUpRootLogger()
    rootFmt = '%(asctime)s:%(levelname)s:%(module)s.%(funcName)s:%(lineno)d:%(message)s'
    flogging.setUpLogger(name='app', folder='app', fmt=rootFmt, level=flogging.LEVEL)
    flogging.setUpLogger(name='ops', folder='operations', fmt='%(message)s', level=flogging.INFO)
    QtCore.qInstallMessageHandler(flogging.qtMessageHandler)

    styleFile = QFile(':/resources/style.css')
    styleFile.open(QFile.ReadOnly)
    styleStr: str = str(styleFile.readAll(), encoding='utf-8')
    app.setStyleSheet(styleStr)
    styleFile.close()

    # Initialize globals and mainWindow
    from dataMole import gui

    mw = gui.window.MainWindow()
    # Create status bar
    gui.statusBar = gui.widgets.statusbar.StatusBar(mw)
    mw.setStatusBar(gui.statusBar)
    gui.notifier = gui.widgets.notifications.Notifier(mw)
    # Set notifier in main window for update
    mw.notifier = gui.notifier
    gui.notifier.mNotifier.updatePosition()
    mw.show()
    sys.exit(app.exec_())
