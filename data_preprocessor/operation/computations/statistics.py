import re
from typing import Dict

from ..interface import SimpleOperation
from ... import data


class AttributeStatistics(SimpleOperation):
    def __init__(self):
        super().__init__()
        self.__attribute: str = None

    def execute(self, df: data.Frame) -> Dict[str, object]:
        desc: Dict[str, object] = df.getRawFrame().loc[:, self.__attribute].describe().to_dict()
        # Rename centiles
        centiles = [(k, v) for k, v in desc.items() if re.fullmatch('.*%', k)]
        for k, v in centiles:
            desc['Centile ' + k] = desc.pop(k)
        # Rename Top and Freq
        if desc.get('top', None) and desc.get('freq', None):
            desc['Most frequent'] = '{} (n={})'.format(desc.pop('top'), desc.pop('freq'))
        # Add Nan count
        nan_count = df.nRows - int(desc['count'])
        del desc['count']
        desc['Nan count'] = '{:d} ({:.5f}%)'.format(nan_count, nan_count / df.nRows * 100)
        if desc.get('mean', None) and desc.get('std', None):
            desc['Mean'] = '{:.5f}'.format(desc.pop('mean'))
            desc['Std'] = '{:.5f}'.format(desc.pop('std'))
        # Uppercase letter
        desc = dict(map(lambda t: (t[0][0].upper() + t[0][1:], t[1]), desc.items()))
        return desc

    def setOptions(self, attribute: str) -> None:
        self.__attribute: str = attribute
