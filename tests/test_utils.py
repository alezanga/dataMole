import numpy as np

from data_preprocessor.operation.utils import joinList, splitString


def test_join_split_list():
    a = [1, 2, -11, 0, np.nan]
    b = joinList(a, sep=' ')
    assert b == '1 2 -11 0 nan'
    c = splitString(b, sep=' ')
    assert c == [str(x) for x in a]

    b = 'w 1 "  1  and 1 " 0 nan str'
    c = splitString(b, sep=' ')
    assert c == ['w', '1', '1  and 1', '0', 'nan', 'str']
    a = joinList(c, sep=' ')
    assert a == 'w 1 "1  and 1" 0 nan str'  # spaces are trimmed
