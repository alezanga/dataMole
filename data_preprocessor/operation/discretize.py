import copy
import logging
from collections import OrderedDict
from enum import Enum
from typing import Iterable, List, Dict, Optional

import sklearn.preprocessing as skp
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
        log = logging.getLogger('graph')
        frame = copy.deepcopy(df)
        sortedAttr = OrderedDict(sorted(self.__attributes.items(), key=lambda t: t[0]))
        columnList = list(sortedAttr.keys())
        binsList = list(sortedAttr.values())
        options = 'OPTIONS:\nColumns: ' + str(columnList) + '\n' + 'NBins: ' + str(binsList)
        f = frame.getRawFrame()
        # Operation ignores nan values
        nanRows = f.iloc[:, columnList].isnull()
        # For every column, transform every non-nan row
        edges = '\nCOMPUTED BINS:\n'
        columns = f.columns
        for col, bins in zip(columnList, binsList):
            nr = nanRows.loc[:, columns[col]]
            discretizer = skp.KBinsDiscretizer(n_bins=bins, encode='ordinal',
                                               strategy=self.__strategy.value)
            f.iloc[(~nr).to_list(), [col]] = discretizer.fit_transform(f.iloc[(~nr).to_list(), [col]])
            edges += 'Bin edges for col {:d}: [{}]\n'.format(col, ', '.join(
                [str(x) for x in discretizer.bin_edges_[0].tolist()]))
        edges = edges.strip('\n')
        sample = '\nSAMPLE:\nOriginal columns:\n' + df.getRawFrame().iloc[:5, columnList].to_string() + \
                 '\nTransformed columns\n: ' + f.iloc[:5, columnList].to_string()
        log.info(options + edges + sample)
        return data.Frame(f)

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
        options['attributes'] = dict()
        for r, bins in self.__attributes.items():
            options['attributes'][r] = {'bins': bins}
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
            errors.append(('Nooption', 'Error: At least one attribute should be selected and filled '
                                       'with options'))
        for r, options in attributes.items():
            bins = options['bins']
            if not isPositiveInteger(bins):
                errors.append(('binsNotInt', 'Error: Number of bins must be a positive integer'))
        if strategy is None:
            errors.append(('missingStrategy', 'Error: Strategy must be set'))
        if errors:
            raise OptionValidationError(errors)
        # Clear attributes
        self.__attributes = dict()
        # Set options
        for r, options in attributes.items():
            k = int(options['bins'])
            self.__attributes[r] = k
        self.__strategy = strategy

    def getEditor(self) -> AbsOperationEditor:
        factory = OptionsEditorFactory()
        factory.initEditor()
        factory.withAttributeTable('attributes', True, False, True,
                                   {'bins': ('K', QIntValidator(0, 10000000))},
                                   types=self.acceptedTypes())
        values = [(s.name, s) for s in BinStrategy]
        factory.withRadioGroup('Select strategy:', 'strategy', values)
        e = factory.getEditor()
        # Set frame model
        e.attributes.setSourceFrameModel(FrameModel(e, self.shapes[0]))
        # Stretch new section
        e.attributes.tableView.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        return e

    def getOutputShape(self) -> Optional[data.Shape]:
        if not self.hasOptions() or self.shapes[0] is None:
            return None
        # Shape does not change
        return self.shapes[0]

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
