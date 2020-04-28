from enum import Enum, unique


@unique
class Types(Enum):
    Categorical = 'category'
    Numeric = 'numeric'
    String = 'string'
    Datetime = 'datetime'


ALL_TYPES = [Types.Numeric, Types.Categorical, Types.String, Types.Datetime]

type_dict = {
    'int64': Types.Numeric,
    'float64': Types.Numeric,
    'datetime64[ns]': Types.Datetime,
    'object': Types.String,
    'category': Types.Categorical
}

inv_type_dict = {
    Types.Numeric: float,
    Types.Datetime: 'datetime64[ns]',
    Types.String: str,
    Types.Categorical: 'category'
}
