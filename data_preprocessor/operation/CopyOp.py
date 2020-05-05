from typing import Optional, List, Tuple

from PySide2.QtWidgets import QComboBox, QWidget

import data_preprocessor.gui.workbench as wb
from data_preprocessor import data
from data_preprocessor.gui.editor.AbsOperationEditor import AbsOperationEditor
from .interface import InputOperation


class CopyOp(InputOperation):
    def __init__(self, workbench: wb.WorkbenchModel):
        super().__init__(workbench)
        self._frame_index: Optional[int] = None

    def execute(self) -> data.Frame:
        """ Get selected dataframe from workbench """
        return self._workbench.getDataframeByIndex(self._frame_index)

    @staticmethod
    def name() -> str:
        return 'Copy operation'

    def info(self) -> str:
        return 'Copy existing dataframe. Should be used as first operation in a pipeline'

    def setOptions(self, selected_frame: int) -> None:
        self._frame_index = selected_frame

    def getOptions(self) -> Tuple[Optional[int], wb.WorkbenchModel]:
        return self._frame_index, self._workbench

    def checkOptions(self) -> Optional[str]:
        if self._frame_index is None:
            return None
        return 'Selection is not valid'

    def inferInputShape(self) -> None:
        if self._frame_index is None:
            self._shape = [None]
        else:
            self._shape = [self._workbench.getDataframeByIndex(self._frame_index).shape]

    def needsOptions(self) -> bool:
        return True

    def getEditor(self) -> AbsOperationEditor:
        class SelectFrame(AbsOperationEditor):
            def getOptions(self) -> List[int]:
                index = self.__selection_box.currentIndex() \
                    if self.__selection_box.currentText() else None
                return [index]

            def setOptions(self, selected_index: Optional[int], workbench: wb.WorkbenchModel) -> None:
                self.__selection_box.setModel(workbench)
                if selected_index is not None:
                    self.__selection_box.setCurrentIndex(selected_index)
                else:
                    self.__selection_box.setCurrentIndex(0)

            def editorBody(self) -> QWidget:
                self.__selection_box = QComboBox(self)
                return self.__selection_box

        return SelectFrame()
