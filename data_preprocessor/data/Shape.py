from typing import List, Union


class Shape:
    """
    Representation of the shape of a Frame
    """
    col_names: List[str] = None
    col_types: List[str] = None
    n_columns: int = None
    n_rows: int = None
    index: Union[str, int] = None

    # Note: in Pandas the index col is not a column of the frame

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def has_index(self) -> bool:
        """
        Return whether index is set
        """
        if self.index is not None:
            return True
        else:
            return False

    def cols_known(self) -> bool:
        """
        Return whether the name and types of every columns is known
        """
        if self.n_columns and self.n_columns >= 0 and self.col_names and self.col_types:
            return True
        else:
            return False
