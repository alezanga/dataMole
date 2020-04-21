from numpy import int64, float64, datetime64

type_dict = {
    'int64': 'numeric',
    'float64': 'numeric',
    'datetime64[ns]': 'date',
    'object': 'str'
}

inv_type_dict = {
    'numeric': float,
    'date': 'datetime64[ns]',
    'str': str
}
