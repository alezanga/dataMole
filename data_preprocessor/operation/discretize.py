import copy
from enum import Enum
from typing import Iterable, List, Dict

from PySide2.QtGui import QIntValidator
from PySide2.QtWidgets import QHeaderView

from data_preprocessor import data
from data_preprocessor.data.types import Types
from data_preprocessor.gui import AbsOperationEditor
from data_preprocessor.gui.frame import FrameModel
from data_preprocessor.gui.generic.OptionsEditorFactory import OptionsEditorFactory
from data_preprocessor.operation.interface.exceptions import OptionValidationError
from data_preprocessor.operation.interface.graph import GraphOperation


class BinStrategy(Enum):
    Uniform = 'uniform'
    Quantile = 'quantile'
    Kmeans = 'kmeans'


class BinsDiscretizer(GraphOperation):
    def __init__(self):
        super().__init__()
        self.__strategy: BinStrategy = BinStrategy.Uniform
        self.__attributes: Dict[int, int] = dict()

    def execute(self, df: data.Frame) -> data.Frame:
        # TODO: define this
        pass

    def acceptedTypes(self) -> List[Types]:
        return [Types.Numeric]

    @staticmethod
    def name() -> str:
        return 'KBinsDiscretizer'

    def shortDescription(self) -> str:
        return 'Discretize numeric values into equal sized bins'

    def hasOptions(self) -> bool:
        return self.__attributes and self.__strategy is not None

    def unsetOptions(self) -> None:
        self.__attributes = dict()

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Iterable:
        options = dict()
        options['attributes'] = copy.deepcopy(self.__attributes)
        options['strategy'] = self.__strategy
        return options

    def setOptions(self, attributes: Dict[int, Dict[str, str]], strategy: BinStrategy) -> None:
        # Validate options
        def isPositiveInteger(x):
            try:
                y = int(x)
            except ValueError:
                return False
            else:
                if y > 0:
                    return True
                return False

        errors = list()
        if not attributes:
            errors.append(('Nooption', 'Error: Select at least one attribute'))
        for r, options in attributes.items():
            bins = options['bins']
            if not isPositiveInteger(bins):
                errors.append(('binsNotInt', 'Error: Number of bins must be a positive integer'))
        if strategy is None:
            errors.append(('missingStrategy', 'Error: Strategy must be set'))
        if errors:
            raise OptionValidationError(errors)
        # Set options
        for r, options in attributes.items():
            k = int(options['bins'])
            self.__attributes[r] = k
        self.__strategy = strategy

    def getEditor(self) -> AbsOperationEditor:
        factory = OptionsEditorFactory()
        factory.initEditor()
        factory.withAttributeTable('attributes', True, False, True,
                                   {'bins': ('K', QIntValidator(0, 10000000))})
        values = [(s.name, s) for s in BinStrategy]
        factory.withRadioGroup('Select strategy:', 'strategy', values)
        e = factory.getEditor()
        # Set frame model
        e.attributes.setSourceFrameModel(FrameModel(e, self.shapes[0]))
        # Stretch new section
        e.attributes.tableView.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        return e

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


export = BinsDiscretizer
