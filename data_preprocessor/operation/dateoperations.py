import datetime as dt
from typing import List, Tuple, Optional, Dict, Set, Union

import pandas as pd
import prettytable as pt
from PySide2.QtCore import Slot, QModelIndex, QAbstractItemModel, QDateTime, QDate, QEvent, QObject, \
    QTime
from PySide2.QtGui import QIcon, Qt, QFontMetrics, QFont
from PySide2.QtWidgets import QWidget, QDateEdit, QGridLayout, \
    QSpacerItem, QPushButton, QVBoxLayout, QSizePolicy, \
    QStyledItemDelegate, QTimeEdit, QCheckBox, QButtonGroup, QHBoxLayout, QAbstractButton, QHeaderView, \
    QTableView, QLineEdit

from data_preprocessor import data, exceptions as exp, flogging
from data_preprocessor.data.types import Types, Type
from data_preprocessor.flogging import Loggable
from data_preprocessor.gui.editor import AbsOperationEditor, OptionsEditorFactory
from data_preprocessor.gui.mainmodels import FrameModel
from data_preprocessor.operation.interface.graph import GraphOperation
from data_preprocessor.operation.utils import splitString, joinList


class DateDiscretizer(GraphOperation, Loggable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # { Attribute index: (timePoints, labels, byDate, byTime) }
        self.__attributes: Dict[int, Tuple[List[pd.Timestamp], List[str], bool, bool]] = dict()
        self.__attributesSuffix: Optional[str] = '_discr'

    def logOptions(self) -> str:
        columns = self.shapes[0].colNames
        tt = pt.PrettyTable(field_names=['Column', 'Intervals', 'Labels', 'byDate', 'byTime'])
        for i, opts in self.__attributes.items():
            timestamps, labels, byDate, byTime = opts
            intervals = list(zip(timestamps, timestamps[1:]))
            if byDate and byTime:
                fmt = _DateIntervalDelegate.DATETIME_FORMAT.replace('_', ' ', 1)
            elif byDate:
                fmt = _DateIntervalDelegate.DATE_FORMAT
            else:
                fmt = _DateIntervalDelegate.TIME_FORMAT
            strIntervals = ['({}, {}]'.format(r[0].strftime(fmt), r[1].strftime(fmt)) for r in intervals]
            tt.add_row([columns[i], '\n'.join(strIntervals), ', '.join(labels), byDate, byTime])
        suffixStr = '\nNew attribute: {} ({:s})'.format(True, self.__attributesSuffix) if \
            self.__attributesSuffix else '\nNew attribute: False'
        return tt.get_string(border=True, vrules=pt.ALL) + suffixStr

    def execute(self, df: data.Frame) -> data.Frame:
        columns = df.colnames
        df = df.getRawFrame().copy(True)

        # Notice that this timestamps are already set to a proper format (with default time/date) by
        # the editor
        intervals: Dict[int, pd.IntervalIndex] = \
            {i: pd.IntervalIndex([pd.Interval(a, b, closed='right') for a, b in zip(opts[0],
                                                                                    opts[0][1:])])
             for i, opts in self.__attributes.items()}

        processedDict = dict()
        for i, opts in self.__attributes.items():
            _, labels, byDate, byTime = opts
            applyCol = df.iloc[:, i]
            if byTime and not byDate:
                # Replace the date part with the default date in a way that every ts has the
                # same date, but retains its original time. Nan values are propagated
                applyCol = applyCol \
                    .map(lambda ts:
                         pd.Timestamp(QDateTime(_IntervalWidget.DEFAULT_DATE,
                                                toQtDateTime(ts.to_pydatetime()).time()).toPython()),
                         na_action='ignore')
            name = columns[i]
            if self.__attributesSuffix:
                name += self.__attributesSuffix
            categoriesMap = dict(zip(intervals[i], labels))
            processedDict[name] = pd.cut(applyCol, bins=intervals[i]).cat.rename_categories(
                categoriesMap)

        if self.__attributesSuffix:
            duplicateColumns: Set[str] = set(processedDict.keys()) & set(columns)
        else:
            duplicateColumns: List[str] = list(processedDict.keys())
        if duplicateColumns:
            df = df.drop(columns=duplicateColumns)
        processed = pd.DataFrame(processedDict).set_index(df.index)

        df = pd.concat([df, processed], ignore_index=False, axis=1)
        if not self.__attributesSuffix:
            # Reorder columns
            df = df[columns]
        return data.Frame(df)

    @staticmethod
    def name() -> str:
        return 'DateDiscretizer'

    @staticmethod
    def shortDescription() -> str:
        return 'Discretize date and times based on ranges'

    def acceptedTypes(self) -> List[Type]:
        return [Types.Datetime]

    def hasOptions(self) -> bool:
        return bool(self.__attributes)

    def unsetOptions(self) -> None:
        self.__attributes = dict()

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Dict[str, Dict[int, Dict[str, List]]]:
        return {
            'selected': {k: {'ranges': (v[0], v[2], v[3]), 'labels': v[1]}
                         for k, v in self.__attributes.items()},
            'suffix': (bool(self.__attributesSuffix), self.__attributesSuffix)
        }

    def setOptions(self, selected: Dict[int, Dict[str, Union[List, Tuple]]],
                   suffix: Tuple[bool, Optional[str]]) -> None:
        errors = list()
        if not selected:
            errors.append(('attribute', 'Error: no attribute is selected'))
        if suffix[0] and not suffix[1]:
            errors.append(('suff', 'Error: suffix is unspecified'))
        selection: Dict[int, Tuple[List[pd.Timestamp], List[str], bool, bool]] = dict()
        for k, opts in selected.items():
            optionsTuple: Tuple[List[pd.Timestamp], bool, bool] = opts.get('ranges', None)
            labels: Optional[List[str]] = opts.get('labels', None)
            if not optionsTuple or not optionsTuple[0]:
                errors.append(('bins', 'Error: bins are not specified at row {:d}'.format(k)))
            if not labels:
                errors.append(('lab', 'Error: no labels are specified at row {:d}'.format(k)))
            if labels and len(set(labels)) != len(labels):
                errors.append(('unique', 'Error: labels are not unique'))
            if optionsTuple:
                bins, byDate, byTime = optionsTuple  # unpack
                if labels and bins and len(labels) != len(bins) - 1:
                    errors.append(('len',
                                   'Error: interval number ({:d}) '
                                   'does not match labels number ({:d}) at row {:d}'
                                   .format(len(bins) - 1, len(labels), k)))
                # byTimeOnly = byTime and not byDate
                selection[k] = bins, labels, byDate, byTime
            if len(errors) > 8:
                # Don't stack to many errors
                break
            # Not necessary to check for overlapping dates, since that is ensured by the delegate
        if errors:
            raise exp.OptionValidationError(errors)

        self.__attributesSuffix = suffix[1] if suffix[0] else None
        self.__attributes = selection

    def getOutputShape(self) -> Optional[data.Shape]:
        if not self.hasOptions() or not self.shapes[0]:
            return None
        s = self.shapes[0].clone()
        attr = list(self.__attributes.keys())
        if self.__attributesSuffix:
            shapeDict: Dict[str, Type] = s.columnsDict
            newCols = [s.colNames[i] + self.__attributesSuffix for i in attr]
            shapeDict.update({c: Types.Ordinal for c in newCols})
            s = data.Shape.fromDict(shapeDict, s.indexDict)
        else:
            s.colTypes = [t if i not in attr else Types.Ordinal for i, t in enumerate(s.colTypes)]
        return s

    def getEditor(self) -> AbsOperationEditor:
        factory = OptionsEditorFactory()
        factory.initEditor()
        factory.withAttributeTable(key='selected', checkbox=True, nameEditable=False, showTypes=True,
                                   options={'ranges': ('Ranges', _DateIntervalDelegate(), None),
                                            'labels': ('Labels', _LabelsDelegate(), None)},
                                   types=self.acceptedTypes())
        factory.withAttributeNameOptionsForTable('suffix')
        return factory.getEditor()

    def injectEditor(self, editor: 'AbsOperationEditor') -> None:
        editor.inputShapes = self.shapes
        editor.selected.setSourceFrameModel(FrameModel(editor, frame=self.shapes[0]))
        hh = editor.selected.tableView.horizontalHeader()
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.Fixed)
        hh.setSectionResizeMode(3, QHeaderView.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.Stretch)
        editor.selected.tableView.setWordWrap(True)
        editor.setSizeHint(800, 500)

    @staticmethod
    def minInputNumber() -> int:
        return 1

    @staticmethod
    def maxInputNumber() -> int:
        return 1

    @staticmethod
    def minOutputNumber() -> int:
        return 1

    @staticmethod
    def maxOutputNumber() -> int:
        return -1


def toQtDateTime(ts: Union[dt.datetime, pd.Timestamp]) -> QDateTime:
    date = QDate(ts.year, ts.month, ts.day)  # y, m, d
    time = QTime(ts.hour, ts.minute, ts.second, (ts.microsecond // 1000))  # h, m, s, ms
    return QDateTime(date, time, Qt.UTC)


class _LabelsDelegate(QStyledItemDelegate):
    def setModelData(self, editor: QLineEdit, model: QAbstractItemModel, index: QModelIndex) -> None:
        text = editor.text()
        strings: List[str] = splitString(text, ' ') if text else list()
        model.setData(index, strings, Qt.EditRole)

    def setEditorData(self, editor: QLineEdit, index: QModelIndex) -> None:
        strings: Optional[List[str]] = index.data(Qt.EditRole)
        if strings:
            editor.setText(joinList(strings, ' '))

    def displayText(self, value: Optional[List[str]], locale) -> str:
        if value:
            return joinList(value, ' ')


class _DateIntervalDelegate(QStyledItemDelegate):
    DATETIME_FORMAT = '%Y-%m-%d_%H:%M'
    DATE_FORMAT = '%Y-%m-%d'
    TIME_FORMAT = '%H:%M'

    def createEditor(self, parent: QWidget, option, index: QModelIndex) -> QWidget:
        # I use an OperationEditor with this delegate, since it already comes with close/accept
        # buttons, description and nice formatting
        self.w = _IntervalWidget(parent)
        self.w.setUpEditor()
        self.w.accept.connect(self.onCommit)
        self.w.reject.connect(self.onReject)
        self.w.setWindowFlags(Qt.Dialog)
        self.w.setWindowModality(Qt.WindowModal)
        columnName = index.model().index(index.row(), index.model().nameColumn, QModelIndex())
        self.w.setWindowTitle('Date intervals: {:s}'.format(columnName.data(Qt.DisplayRole)))
        self.w.setDescription(
            'Define the bin edges as dates or datetimes. Intervals are right-inclusive',
            long='If date or time components are not both required they can be disabled.<br>'
                 'Time points must define a strictly increasing time series, since they describe '
                 'contiguous ranges')
        self.w.setFocusPolicy(Qt.StrongFocus)  # Advised by docs
        return self.w

    @Slot()
    def onCommit(self) -> None:
        self.commitData.emit(self.w)
        # self.onReject()

    @Slot()
    def onReject(self) -> None:
        self.closeEditor.emit(self.w, QStyledItemDelegate.NoHint)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj is not self.w:
            return False
        if event.type() == QEvent.WindowDeactivate or event.type() == QEvent.WindowActivate or \
                event.type() == QEvent.FocusOut or event.type() == QEvent.FocusIn:
            return False
        return super().eventFilter(obj, event)

    def setEditorData(self, editor: '_IntervalWidget', index: QModelIndex) -> None:
        bins: List[pd.Timestamp]
        obj = index.data(Qt.EditRole)
        if obj:
            bins, byDate, byTime = index.data(Qt.EditRole)
            if bins:
                dataBins: List[QDateTime] = list(map(toQtDateTime, bins))
                editor.setOptions(dataBins, byDate, byTime)
                return
        # Make two row by default (minimum required to define a range)
        editor.addRow()
        editor.addRow()

    def setModelData(self, editor: '_IntervalWidget', model: QAbstractItemModel,
                     index: QModelIndex) -> None:
        datetimes: List[QDateTime]
        datetimes, byDate, byTime = editor.getOptions()
        # Do some validation
        errors = list()
        if len(datetimes) < 2:
            errors.append(('e1', 'Error: at least one range must be defined'))
        if any([a >= b for a, b in zip(datetimes, datetimes[1:])]):
            errors.append(('e2', 'Error: datetime points must be strictly increasing'))
        if errors:
            editor.handleErrors(errors)
            # Avoid setting options and leave editor open
            return
        options = ([pd.Timestamp(date.toPython(), tz='UTC') for date in datetimes], byDate, byTime)
        model.setData(index, options, Qt.EditRole)
        # Resize rows. This assumes that the TableView is the delegate parent
        f = QFontMetrics(QFont())
        rowHeight = f.height() * len(options[0])
        table: QTableView = self.parent()
        table.setRowHeight(index.row(), rowHeight)
        # Close editor. Works because it's the delegate that tells the view to close it with this signal
        self.closeEditor.emit(self.w, QStyledItemDelegate.NoHint)

    def displayText(self, value: Tuple[List[pd.Timestamp], bool, bool], locale) -> str:
        # Display only relevant part (time/date/both)
        timestamps, byDate, byTime = value
        fmt = self.DATE_FORMAT if not byTime else self.TIME_FORMAT if not byDate \
            else self.DATETIME_FORMAT
        pairs: List[Tuple[pd.Timestamp, pd.Timestamp]] = list(zip(timestamps, timestamps[1:]))
        strings: List[str] = ['({}, {}]'.format(t[0].strftime(fmt), t[1].strftime(fmt)) for t in pairs]
        return '  '.join(strings)


class _IntervalWidget(AbsOperationEditor):
    _SPACER: int = 40
    DEFAULT_DATE = QDate(1900, 1, 1)
    DEFAULT_TIME = QTime(0, 0, 0, 0)

    def editorBody(self) -> QWidget:
        self.body = _Widget(self)
        self.body.group.buttonToggled[QAbstractButton, bool].connect(self.checkboxToggled)
        self.body.addRowBut.clicked.connect(self.addRow)
        self.__layoutRows: List[int] = list()  # Important to initialize before addRow()
        self.__timeVisible: bool = True
        self.__dateVisible: bool = True
        return self.body

    def setOptions(self, bins: List[QDateTime], byDate: bool, byTime: bool) -> None:
        for b in bins:
            d, t = self.addRow()
            d.setDate(b.date())
            t.setTime(b.time())
        if not (byDate or byTime):
            # All checked by default
            byDate = True
            byTime = True
        self.body.byDate.setChecked(byDate)
        self.body.byTime.setChecked(byTime)

    def getOptions(self) -> Tuple[List[QDateTime], bool, bool]:
        dates = list()
        byTime: bool = self.body.byTime.isChecked()
        byDate: bool = self.body.byDate.isChecked()
        for row in self.__layoutRows:
            date: QDate = self.body.gLayout.itemAtPosition(row, 0).widget().date()
            time: QTime = self.body.gLayout.itemAtPosition(row, 2).widget().time()
            if byDate and byTime:
                datetime = QDateTime(date, time, Qt.UTC)
            elif not byTime:
                # Date only
                datetime = QDateTime(date, self.DEFAULT_TIME, Qt.UTC)
            elif not byDate:
                # Time only
                datetime = QDateTime(self.DEFAULT_DATE, time, Qt.UTC)
            else:
                flogging.appLogger.error(
                    'Invalid byDate/byTime combination: {}, {}'.format(byDate, byTime))
                raise ValueError('Unexpected error: unsupported datetime input arguments')
            dates.append(datetime)
        return dates, byDate, byTime

    def showTime(self) -> None:
        for row in self.__layoutRows:
            self.body.gLayout.addItem(QSpacerItem(self._SPACER, 0), row, 1)
            self.body.gLayout.itemAtPosition(row, 2).widget().show()
        self.__timeVisible = True

    def showDate(self) -> None:
        for row in self.__layoutRows:
            self.body.gLayout.addItem(QSpacerItem(self._SPACER, 0), row, 1)
            self.body.gLayout.itemAtPosition(row, 0).widget().show()
        self.__dateVisible = True

    def hideTime(self) -> None:
        for row in self.__layoutRows:
            self.body.gLayout.removeItem(self.body.gLayout.itemAtPosition(row, 1))
            self.body.gLayout.itemAtPosition(row, 2).widget().hide()
        self.__timeVisible = False

    def hideDate(self) -> None:
        for row in self.__layoutRows:
            self.body.gLayout.removeItem(self.body.gLayout.itemAtPosition(row, 1))
            self.body.gLayout.itemAtPosition(row, 0).widget().hide()
        self.__dateVisible = False

    @Slot(QAbstractButton, bool)
    def checkboxToggled(self, checkbox: QCheckBox, checked: bool) -> None:
        if not checked and self.body.group.checkedId() == -1:
            # No button checked, restore previous state and do nothing
            checkbox.setChecked(True)
        else:
            if checkbox is self.body.byTime and checked != self.__timeVisible:
                if checked:
                    self.showTime()
                else:
                    self.hideTime()
            elif checkbox is self.body.byDate and checked != self.__dateVisible:
                if checked:
                    self.showDate()
                else:
                    self.hideDate()

    @Slot()
    def addRow(self) -> (QDateEdit, QTimeEdit):
        # New row should be the successor of the last one
        row: int = max(self.__layoutRows) + 1 if self.__layoutRows else 0
        a = QDateEdit(self)
        b = QTimeEdit(self)
        a.setFixedHeight(30)
        b.setFixedHeight(30)
        a.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        b.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.body.gLayout.addWidget(a, row, 0)
        self.body.gLayout.addItem(QSpacerItem(self._SPACER, 0), row, 1)
        self.body.gLayout.addWidget(b, row, 2)
        self.body.gLayout.addItem(QSpacerItem(self._SPACER, 0), row, 3)
        # Create a button to remove row
        removeBut = QPushButton(QIcon('data_preprocessor/style/icons/close.png'), '', self)
        removeBut.setFixedSize(30, 30)
        removeBut.setToolTip('Remove row')
        # Lambda here is ok since it's called from main thread, so even if it's not a slot it's safe
        removeBut.clicked.connect(lambda: self.removeRow(row))
        self.body.gLayout.addWidget(removeBut, row, 4)
        # Hide time if it's not wanted
        if not self.__timeVisible:
            self.body.gLayout.removeItem(self.body.gLayout.itemAtPosition(row, 1))
            b.hide()
        if not self.__dateVisible:
            self.body.gLayout.removeItem(self.body.gLayout.itemAtPosition(row, 1))
            a.hide()
        self.__layoutRows.append(row)
        return a, b

    @Slot(int)
    def removeRow(self, row: int) -> None:
        self.body.gLayout.itemAtPosition(row, 0).widget().deleteLater()
        self.body.gLayout.removeItem(self.body.gLayout.itemAtPosition(row, 1))
        self.body.gLayout.itemAtPosition(row, 2).widget().deleteLater()
        self.body.gLayout.removeItem(self.body.gLayout.itemAtPosition(row, 3))
        self.body.gLayout.itemAtPosition(row, 4).widget().deleteLater()
        self.__layoutRows.remove(row)


class _Widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mainLayout = QVBoxLayout(self)
        self.byTime = QCheckBox('By time', self)
        self.byDate = QCheckBox('By date', self)
        self.group = QButtonGroup(self)
        butLayout = QHBoxLayout()
        butLayout.addWidget(self.byDate)
        butLayout.addWidget(self.byTime)
        self.group.addButton(self.byDate)
        self.group.addButton(self.byTime)
        self.addRowBut = QPushButton('Add interval', self)
        self.addRowBut.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.gLayout = QGridLayout()
        self.mainLayout.addLayout(butLayout)
        self.mainLayout.addWidget(self.addRowBut, 0, Qt.AlignLeft)
        self.mainLayout.addLayout(self.gLayout)
        self.group.setExclusive(False)
        self.byDate.setChecked(True)
        self.byTime.setChecked(True)


export = DateDiscretizer
