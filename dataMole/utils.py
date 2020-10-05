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

from functools import wraps

import shiboken2
from PySide2.QtCore import QObject


def singleton(cls):
    """Make a class a Singleton class (only one instance)"""

    @wraps(cls)
    def wrapper_singleton(*args, **kwargs):
        if not wrapper_singleton.instance:
            wrapper_singleton.instance = cls(*args, **kwargs)
        return wrapper_singleton.instance

    wrapper_singleton.instance = None
    return wrapper_singleton


@singleton
class UIdGenerator:
    def __init__(self):
        self.__lastId: int = 0

    def getUniqueId(self) -> int:
        self.__lastId = self.__lastId + 1
        return self.__lastId


def safeDelete(obj: QObject) -> None:
    """ Calls deleteLater() on a QObject, doing nothing if the object was already deleted """
    if obj and shiboken2.isValid(obj):
        obj.deleteLater()
