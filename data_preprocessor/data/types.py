from enum import Enum, unique


@unique
class Types(Enum):
    Categorical = 'categorical'
    Numeric = 'numeric'
    String = 'string'
    Datetime = 'datetime'


ALL_TYPES = [Types.Numeric, Types.Categorical, Types.String, Types.Datetime]

type_dict = {
    'int64': Types.Numeric,
    'float64': Types.Numeric,
    'datetime64[ns]': Types.Datetime,
    'object': Types.String
}

inv_type_dict = {
    Types.Numeric: float,
    Types.Datetime: 'datetime64[ns]',
    Types.String: str
}
