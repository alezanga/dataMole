import abc
from typing import List
from PySide2.QtWidgets import QWidget, QDialog


class AbsStepEditor(QDialog):
    @abc.abstractmethod
    def getOptions(self) -> List:
        """
        Return the arguments read by the editor panel in the same order as they were added to the editor
        :return:
        """
        pass
