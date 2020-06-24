from typing import Dict, List

import numpy
import pandas as pd


def numpy_equal(a: numpy.array, b: numpy.array) -> bool:
    return ((a == b) | ((a != a) & (b != b))).all()


def nan_to_None(d: Dict[str, List]) -> Dict[str, List]:
    """ Takes a dictionary dataframe with nan values and convert them to None. Useful for testing """
    r = dict()
    for name, values in d.items():
        new_values = list(map(lambda v: None if pd.isna(v) else v, values)) if values else list()
        r[name] = new_values
    return r
