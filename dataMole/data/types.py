import abc
from typing import Union

import numpy as np
import pandas as pd

from dataMole.utils import singleton


class Type(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def code(self) -> int:
        pass

    @staticmethod
    def fromCode(code: int) -> 'Type':
        return {v.code: v for k, v in Types.__dict__.items() if hasattr(v, 'code')}[code]

    def __eq__(self, other) -> bool:
        return self.code == other.code

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.name)

    def __deepcopy__(self, memodict=None) -> 'Type':
        # Disable deepcopy
        return self


class Categorical(Type):
    pass


@singleton
class Datetime(Type):
    @property
    def name(self) -> str:
        return 'Datetime'

    @property
    def code(self) -> int:
        return 4


@singleton
class Ordinal(Categorical):
    @property
    def name(self) -> str:
        return 'Ordinal'

    @property
    def code(self) -> int:
        return 3


@singleton
class Nominal(Categorical):
    @property
    def name(self) -> str:
        return 'Nominal'

    @property
    def code(self) -> int:
        return 2


@singleton
class Numeric(Type):
    @property
    def name(self) -> str:
        return 'Numeric'

    @property
    def code(self) -> int:
        return 1


@singleton
class String(Type):
    @property
    def name(self) -> str:
        return 'String'

    @property
    def code(self) -> int:
        return 0


class IndexType(Type):
    def __init__(self, iType: Type):
        super().__init__()
        self.__type = iType

    @property
    def name(self) -> str:
        return self.__type.name

    @property
    def type(self) -> Type:
        return self.__type

    @property
    def code(self) -> int:
        return self.__type.code

    def __eq__(self, other) -> bool:
        return isinstance(other, IndexType) and self.__type == other.__type

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash((self.name, self.__type))


class Types:
    Ordinal = Ordinal()
    Nominal = Nominal()
    Numeric = Numeric()
    String = String()
    Datetime = Datetime()


ALL_TYPES = [Types.Numeric, Types.String, Types.Datetime, Types.Nominal, Types.Ordinal]


def wrapperType(dataType: Union[np.dtype, type]) -> Type:
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
