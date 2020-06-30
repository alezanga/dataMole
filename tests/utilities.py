import collections
from typing import Any

import numpy
import pandas as pd


def numpy_equal(a: numpy.array, b: numpy.array) -> bool:
    return ((a == b) | ((a != a) & (b != b))).all()


def nan_to_None(val: Any) -> Any:
    """ Takes a scalar value or a container with nan values and convert them to None. Useful
    for testing. Supports dict, list, tuple, set, iterators and strings (considered scalar)

    :param val: container or value to convert
    :return a copy of the container with nan values replaced with None
    :raise NotImplementedError if it encounters iterable objects with unsupported type
    """
    if isinstance(val, str) or not isinstance(val, collections.abc.Iterable):
        # It's a scalar
        return None if pd.isna(val) else val
    # If it's a sequence recursively process each entry
    if isinstance(val, dict):
        return {k: nan_to_None(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [nan_to_None(v) for v in val]
    elif isinstance(val, tuple):
        return tuple(nan_to_None(list(val)))
    elif isinstance(val, collections.Iterator):
        return (nan_to_None(v) for v in val)
    elif isinstance(val, set):
        return {nan_to_None(v) for v in val}
    else:
        raise NotImplementedError('Object \'{}\' of type \'{}\' is not supported'.format(val, type(val)))
