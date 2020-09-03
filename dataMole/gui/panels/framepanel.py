from PySide2.QtCore import Slot, QAbstractItemModel, Qt, Signal
from PySide2.QtWidgets import QWidget, QLabel, QFormLayout, QComboBox, QPushButton, \
    QVBoxLayout, QSizePolicy

from dataMole.gui.mainmodels import FrameModel
from dataMole.gui.workbench import WorkbenchModel


class FramePanel(QWidget):
    operationRequest = Signal(type)  # Operation type

    def __init__(self, w: WorkbenchModel, opModel: QAbstractItemModel, parent=None):
        super().__init__(parent)
        self.__workbench: WorkbenchModel = w
        labeln = QLabel('Name:', self)
        labelc = QLabel('Columns:', self)
        labelr = QLabel('Rows:', self)
        labeli = QLabel('Index:', self)
        self.name = QLabel(self)
        self.name.setWordWrap(True)
        self.rows = QLabel(self)
        self.columns = QLabel(self)
        self.index = QLabel(self)
        self.__currentFrameModel: FrameModel = None
        fLayout = QFormLayout()
        fLayout.addRow(labeln, self.name)
        fLayout.addRow(labelr, self.rows)
        fLayout.addRow(labelc, self.columns)
        fLayout.addRow(labeli, self.index)
        fLayout.setVerticalSpacing(0)

        lab = QLabel('Select an operation:')
        lab.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.operationsComboBox = QComboBox(self)
        self.operationsComboBox.setModel(opModel)
        applyButton = QPushButton('Apply', self)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.addLayout(fLayout)
        layout.addWidget(lab, 0, Qt.AlignBottom)
        layout.addWidget(self.operationsComboBox)
        layout.addWidget(applyButton)
        applyButton.clicked.connect(self.applyOperation)

    @Slot()
    def applyOperation(self) -> None:
        data: type = self.operationsComboBox.model() \
            .item(self.operationsComboBox.currentIndex(), 0).data(Qt.UserRole)
        self.operationRequest.emit(data)

    @Slot()
    def updateData(self) -> None:
        if self.__currentFrameModel:
            name = self.__currentFrameModel.name
            self.name.setText(name)
            self.columns.setText(str(self.__currentFrameModel.columnCount()))
            self.rows.setText(str(self.__currentFrameModel.rowCount()))
            shape = self.__currentFrameModel.frame.shape
            self.index.setText(shape.index[0] if len(shape.index) == 1 else
                               '[{}]'.format(','.join(shape.index)))
        else:
            self.name.setText('')
            self.columns.setText('')
            self.rows.setText('')
            self.index.setText('')

    @Slot(str, str)
    def onFrameSelectionChanged(self, selected: str, *_) -> None:
        if selected:
            if self.__currentFrameModel:
                # Disconnect all signal in model from this widget
                self.__currentFrameModel.disconnect(self)
            # Set new model
            self.__currentFrameModel = self.__workbench.getDataframeModelByName(selected)
            # Connect
            self.__currentFrameModel.rowsRemoved.connect(self.updateData)
            self.__currentFrameModel.rowsInserted.connect(self.updateData)
            self.__currentFrameModel.columnsRemoved.connect(self.updateData)
            self.__currentFrameModel.columnsInserted.connect(self.updateData)
            self.__currentFrameModel.modelReset.connect(self.updateData)
            self.__workbench.dataChanged.connect(self.updateData)
        else:
            self.__currentFrameModel = None
        # Update current info
        self.updateData()
