import collections
from typing import Any, Dict, List

import pandas as pd


def roundValues(val: Dict[Any, List], decimals: int) -> Dict[Any, List]:
    """ Round every float in 'val' to a number with specified number of decimal digits """
    return {k: [round(e, decimals) if isinstance(e, float) else e for e in v] for k, v in val.items()}


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


def isDictDeepCopy(a: Dict, b: Dict) -> bool:
    if a != b or (a is b and not isinstance(a, (dict, list, set, tuple)) and \
                  not isinstance(b, (dict, list, set, tuple))):
        return True
    if a is b:
        return False
    fieldsA = set(a.keys())
    fieldsB = set(b.keys())
    intersection = fieldsA & fieldsB
    return all([isDictDeepCopy(a[name], b[name]) for name in intersection])
