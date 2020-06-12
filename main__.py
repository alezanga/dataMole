import copy
import sys
from pprint import pprint

from PySide2.QtGui import QIntValidator
from PySide2.QtWidgets import QApplication

from data_preprocessor.data import Frame
from data_preprocessor.gui.mainmodels import FrameModel
from data_preprocessor.gui.generic.OptionsEditorFactory import OptionsEditorFactory

if __name__ == "__main__":
    d = {'col1': [1, 2, 3, 4.0, 10], 'col2': [3, 4, 5, 6, 0], 'col3': ['q', 2, 'q', 'q', 2],
         'date': ['05-09-1988', '22-12-1994', '21-11-1995', '22-06-1994', '12-12-2012']}
    app = QApplication([])
    pw = OptionsEditorFactory()
    pw.initEditor()
    pw.withCheckBox('Select?', 'check1')
    pw.withCheckBox('Select2?', 'check2')
    pw.withRadioGroup('Radio:', 'rad', [('Choiche1', 'WERTYU'), ('Second', 1)])
    pw.withTextField('Vales to merge', 'mergeVal', QIntValidator())
    tableOptions = {
        'bins': ('Bins', QIntValidator()),
        'You': ('Yt', None)
    }
    pw.withAttributeTable(True, False, False, tableOptions)
    e = pw.getEditor()
    e.attributeTable.setSourceFrameModel(FrameModel(e, Frame(d)))
    options = {
        'check1': False,
        'check2': False,
        'rad': 1,
        'mergeVal': 'yes',
        'attributeTable': {
            1: {'bins': 'Newson'},
            3: {'You': 53}
        }
    }
    e.setOptions(**copy.deepcopy(options))
    e.show()
    app.exec_()
    pprint(e.getOptions())
    sys.exit()
