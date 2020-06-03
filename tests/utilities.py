from typing import Dict, List

import pandas as pd


def nan_to_None(d: Dict[str, List]) -> Dict[str, List]:
    """ Takes a dictionary dataframe with nan values and convert them to None. Useful for testing """
    r = dict()
    for name, values in d.items():
        new_values = list(map(lambda v: None if pd.isna(v) else v, values)) if values else list()
        r[name] = new_values
    return r
