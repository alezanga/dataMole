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

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QWidget

from dataMole.gui.editor import AbsOperationEditor
from dataMole.operation.interface.operation import Operation


def configureEditor(editor: AbsOperationEditor, op: Operation, parent: QWidget = None):
    """ Configure an editor with standard fields and window size """
    # Configure standard fields
    editor.setWindowTitle(op.name())
    editor.setDescription(op.shortDescription(), op.longDescription())
    editor.acceptedTypes = op.acceptedTypes()
    editor.workbench = op.workbench
    editor.inputShapes = op.shapes if hasattr(op, 'shapes') else list()
    # Set parent and flags
    editor.setParent(parent)
    editor.setWindowFlags(Qt.Window)
    editor.setWindowModality(Qt.ApplicationModal)


def configureEditorOptions(editor: AbsOperationEditor, op: Operation):
    """ Adds options to the editor """
    # Set options
    options = op.getOptions()
    if isinstance(options, dict):
        editor.setOptions(**options)
    else:
        editor.setOptions(*options)
