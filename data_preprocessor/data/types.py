from enum import Enum, unique
from typing import Union

import numpy as np
import pandas as pd


@unique
class Types(Enum):
    Ordinal = 'ordinal'
    Nominal = 'nominal'
    Numeric = 'numeric'
    String = 'string'
    Datetime = 'datetime'


ALL_TYPES = [Types.Numeric, Types.String, Types.Datetime, Types.Nominal, Types.Ordinal]


def displayedType(dataType: Union[np.dtype, type]) -> Types:
    if pd.api.types.is_datetime64_any_dtype(dataType):
        return Types.Datetime
    elif pd.api.types.is_numeric_dtype(dataType):
        return Types.Numeric
    elif pd.api.types.is_categorical_dtype(dataType):
        dataType: pd.CategoricalDtype
        if dataType.ordered is True:
            return Types.Ordinal
        else:
            return Types.Nominal
    elif pd.api.types.is_string_dtype(dataType) or pd.api.types.is_object_dtype(dataType):
        return Types.String
    else:
        return dataType.name
