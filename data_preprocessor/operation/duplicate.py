from typing import Dict, Tuple, List, Optional

import prettytable as pt
from PySide2.QtWidgets import QHeaderView

from data_preprocessor import data, exceptions as exp, flogging
from data_preprocessor.gui.editor import AbsOperationEditor, OptionsEditorFactory, \
    OptionValidatorDelegate
from data_preprocessor.gui.mainmodels import FrameModel
from data_preprocessor.operation.interface.graph import GraphOperation
from data_preprocessor.operation.utils import SingleStringValidator


class DuplicateColumn(GraphOperation, flogging.Loggable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__attributes: Dict[int, str] = dict()

    def logOptions(self) -> Optional[str]:
        tt = pt.PrettyTable(field_names=['Column to duplicate', 'New name'])
        columns = self.shapes[0].colNames
        for a, n in self.__attributes.items():
            tt.add_row([columns[a], n])
        return tt.get_string(border=True, vrules=pt.ALL)

    def execute(self, df: data.Frame) -> data.Frame:
        f = df.getRawFrame().copy(True)
        pairs: List[Tuple[int, str]] = list(self.__attributes.items())
        names = [v[1] for v in pairs]
        indexes = [v[0] for v in pairs]
        f[names] = f.iloc[:, indexes]
        return data.Frame(f)

    @staticmethod
    def name() -> str:
        return 'DuplicateColumn'

    @staticmethod
    def shortDescription() -> str:
        return 'Makes duplicates of selected columns, giving them a new name'

    def hasOptions(self) -> bool:
        return bool(self.__attributes)

    def unsetOptions(self) -> None:
        self.__attributes = dict()

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Dict[str, Dict[int, Dict[str, str]]]:
        return {'table': {a: {'rename': name} for a, name in self.__attributes.items()}}

    def setOptions(self, table: Dict[int, Dict[str, str]]) -> None:
        errors = list()
        if not table:
            errors.append(('no', 'Error: at least one column should be selected'))
        elif not table.values():
            errors.append(('values', 'Error: selected columns target names are not set'))
        else:
            names: Dict[int, str] = {i: d.get('rename', ' ').strip() for i, d in table.items()}
            nameList = list(names.values())
            if not all(nameList):
                errors.append(('set', 'Error: some names are not set'))
            if len(set(nameList)) != len(nameList):
                errors.append(('set', 'Error: some column names are duplicate'))
        if errors:
            raise exp.OptionValidationError(errors)
        self.__attributes = names

    def getEditor(self) -> AbsOperationEditor:
        factory = OptionsEditorFactory()
        factory.initEditor()
        factory.withAttributeTable(key='table',
                                   checkbox=True,
                                   nameEditable=False,
                                   showTypes=True,
                                   options={'rename': ('New name',
                                                       OptionValidatorDelegate(SingleStringValidator()),
                                                       None)},
                                   types=self.acceptedTypes())
        return factory.getEditor()

    def injectEditor(self, editor: 'AbsOperationEditor') -> None:
        # Set frame model from shape
        editor.table.setSourceFrameModel(FrameModel(editor, self.shapes[0]))
        # Stretch new section
        editor.table.tableView.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

    def getOutputShape(self) -> Optional[data.Shape]:
        if not self.hasOptions() or not self.shapes[0]:
            return None
        s = self.shapes[0].clone()
        types = self.shapes[0].colTypes
        s.colNames.extend([n for n in self.__attributes.values()])
        s.colTypes.extend([types[i] for i in self.__attributes.keys()])
        return s

    @staticmethod
    def minInputNumber() -> int:
        return 1

    @staticmethod
    def maxInputNumber() -> int:
        return 1

    @staticmethod
    def minOutputNumber() -> int:
        return 1

    @staticmethod
    def maxOutputNumber() -> int:
        return -1


export = DuplicateColumn