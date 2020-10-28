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

from abc import ABC
from typing import Optional


class Loggable(ABC):
    def __init__(self):
        super().__init__()
        self._logExecutionString: str = None
        self._logOptionsString: str = None

    def logOptions(self) -> Optional[str]:
        """
        Return a string which logs the options set in an operation, or None if no option are used.
        By default returns the field _logOptionsString
        """
        return self._logOptionsString

    def logMessage(self) -> Optional[str]:
        """
        Return the formatted message to log after an operation completes. Should include details about
        the execution, like learned parameters or anything that can only be known inside the
        :func:`~dataMole.operation.interface.graph.GraphOperation.execute` method. By
        default returns the parameter _logExecutionString """
        return self._logExecutionString
