import re
from typing import List

from PySide2.QtCore import QRegExp, QLocale
from PySide2.QtGui import QRegExpValidator, QValidator, QIntValidator, QDoubleValidator

doubleListValidator = QRegExpValidator(QRegExp('(\\d+(\\.\\d)?\\d*)(\\,\\s?(\\d+(\\.\\d)?\\d*))*'))


def splitList(string: str, sep: str) -> List[str]:
    """
    Split a string on a separator, trimming spaces. Parts within double quotes are not parsed

    :param string: string to split
    :param sep: the separator string (or single char)
    :return: the list resulting from split
    """
    string = string.strip(' ')
    sepPattern = '\\s*{}\\s*'.format(sep)
    # Split on separator
    listS = re.split('({})(?=(?:"[^"]*"|[^"])*$)'.format(sepPattern), string)
    # Filter away separators
    listS = [s.strip('"') for s in listS if not re.fullmatch(sepPattern, s)]
    return listS


class NumericListValidator(QValidator):
    """ QValidator for space-separated list of numbers. Works with float or ints """

    def __init__(self, float_int: type, parent=None):
        super().__init__(parent)
        if float_int is int:
            self.__numValidator = QIntValidator(self)
        elif float_int is float:
            self.__numValidator = QDoubleValidator(self)

    def validate(self, inputString: str, pos: int) -> QValidator.State:
        self.__numValidator.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        inputString = inputString.strip(' ')
        stringList: List[str] = inputString.split(' ')
        for string in stringList:
            if self.__numValidator.validate(string, 0)[0] == QValidator.Invalid:
                return QValidator.Invalid
        return QValidator.Acceptable


class MixedListValidator(QValidator):
    # _regexp = QRegExp('((\\S+)|(\'.+\'))({}((\\S+)|(\'.+\')))*')

    def __init__(self, sep: str, parent=None):
        super().__init__(parent)
        self.__sep = sep
        self.__regexp = '[^\']*'

    def validate(self, inputString: str, pos: int) -> QValidator.State:
        inputString = inputString.strip(' ')
        if re.fullmatch(self.__regexp, inputString):
            return QValidator.Acceptable
        else:
            match = re.match(self.__regexp, inputString)
            if match and len(match.group(0)) == len(inputString):
                return QValidator.Intermediate
        return QValidator.Invalid
        # if self._regexp.exactMatch(inputString):
        #     return QValidator.Acceptable
        # elif self._regexp.matchedLength() == len(inputString):
        #     return QValidator.Intermediate
        # pos = len(inputString)
        # return QValidator.Invalid


class ManyMixedListsValidator(QValidator):
    """ Validates a list of lists, where each value in a list is space separated and every list is
    semicolon separated """

    def validate(self, inputString: str, pos: int) -> QValidator.State:
        inputString = inputString.strip(' ')
        lists = splitList(inputString, sep=';')
        val = MixedListValidator(sep='\\s')
        for s in lists:
            if val.validate(s, 0) == QValidator.Invalid:
                return QValidator.Invalid
        return QValidator.Acceptable
