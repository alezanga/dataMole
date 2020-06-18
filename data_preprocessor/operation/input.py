from typing import Optional, List, Union

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QComboBox, QWidget

from data_preprocessor import data
from data_preprocessor.gui.editor.interface import AbsOperationEditor
from .interface.graph import InputGraphOperation


class CopyOp(InputGraphOperation):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._frame_name: Optional[str] = None

    def execute(self) -> data.Frame:
        """ Get selected dataframe from workbench """
        return self._workbench.getDataframeModelByName(self._frame_name).frame

    @staticmethod
    def name() -> str:
        return 'Copy operation'

    def shortDescription(self) -> str:
        return 'Copy existing dataframe. Should be used as first operation in a pipeline'

    def hasOptions(self) -> bool:
        return bool(self._frame_name)

    def setOptions(self, selected_frame: str) -> None:
        self._frame_name = selected_frame

    def getOptions(self) -> List[Optional[str]]:
        return [self._frame_name]

    def getOutputShape(self) -> Union[data.Shape, None]:
        if not self.hasOptions():
            return None
        else:
            return self._workbench.getDataframeModelByName(self._frame_name).frame.shape

    def needsOptions(self) -> bool:
        return True

    def getEditor(self) -> AbsOperationEditor:
        class SelectFrame(AbsOperationEditor):
            def getOptions(self) -> List[str]:
                name = self.__selection_box.currentText() if self.__selection_box.currentText() else None
                return [name]

            def setOptions(self, selected_name: Optional[str]) -> None:
                self.__selection_box.setModel(self.workbench)
                if selected_name is not None:
                    self.__selection_box.setCurrentIndex(
                        self.__selection_box.findText(selected_name, Qt.MatchExactly))
                else:
                    self.__selection_box.setCurrentIndex(0)

            def editorBody(self) -> QWidget:
                self.__selection_box = QComboBox(self)
                return self.__selection_box

        return SelectFrame()


export = CopyOp
