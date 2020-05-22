import re
from typing import Dict

from ..interface.operation import Operation
from ... import data
from ...data.types import Types


class AttributeStatistics(Operation):
    def __init__(self):
        super().__init__()
        self.__attribute: int = -1

    def execute(self, df: data.Frame) -> Dict[str, object]:
        desc: Dict[str, object] = df.getRawFrame().iloc[:, self.__attribute].describe().to_dict()
        # Rename centiles
        centiles = [(k, v) for k, v in desc.items() if re.fullmatch('.*%', k)]
        for k, v in centiles:
            desc['Centile ' + k] = desc.pop(k)
        # Rename Top and Freq
        if desc.get('top', None) is not None and desc.get('freq', None) is not None:
            desc['Most frequent'] = '{} (n={})'.format(desc.pop('top'), desc.pop('freq'))
        # Add Nan count
        nan_count = df.nRows - int(desc['count'])
        del desc['count']
        desc['Nan count'] = '{:d} ({:.2f}%)'.format(nan_count, nan_count / df.nRows * 100)
        if desc.get('mean', None) is not None and desc.get('std', None) is not None:
            desc['Mean'] = '{:.3f}'.format(desc.pop('mean'))
            desc['Std'] = '{:.3f}'.format(desc.pop('std'))
        # Uppercase letter
        desc = dict(map(lambda t: (t[0][0].upper() + t[0][1:], t[1]), desc.items()))
        return desc

    def setOptions(self, attribute: int) -> None:
        self.__attribute: int = attribute


class Hist(Operation):
    def __init__(self):
        super().__init__()
        self.__attribute: int = None
        self.__type: Types = None
        self.__nBins: int = None

    def execute(self, df: data.Frame) -> Dict[object, int]:
        col = df.getRawFrame().iloc[:, self.__attribute]
        if self.__type == Types.Numeric:
            values = col.value_counts(bins=self.__nBins, sort=False)
            values.index = values.index.map(lambda i: '{:.2f}'.format(i.left))
            return values.to_dict()
        else:
            return col.value_counts().to_dict()

    def setOptions(self, attribute: int, attType: Types, bins: int = None) -> None:
        self.__attribute = attribute
        self.__type = attType
        self.__nBins = bins if bins else None
