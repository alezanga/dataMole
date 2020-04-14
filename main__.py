import pandas as pd

from data_preprocessor.data.Frame import Frame

if __name__ == "__main__":
    # app = QApplication([])
    #
    # factory = StepEditorFactory()
    # factory.initEditor()
    # factory.addComboBox('combo box', QStringListModel(['1', 'ciao']), 'Tooltip')
    # factory.addTextField('field')
    # factory.addCheckBox('Checkbox', 'Tooltipwww')
    # factory.setSizeHint(1000, 300)
    #
    # editor = factory.getEditor()
    #
    # values = editor.show()
    #
    # app.exec_()
    #
    # values = editor.getOptions()
    # print(values)

    # f = Frame()
    # f.load('../datasets/iris.csv', 0, ',', ['?'])
    # # f.head()
    # f['sepal_sum'] = f.apply(lambda row: row['sepal_length'] + row['sepal_width'])

    # f.head()
    d = {'col1': [1, 2, 0.5, 4, 10], 'col2': [3, 4, 5, 6, 0]}
    f = Frame(d)
    f = f[f['col1'] > 3]
    # heads = f.headers()
    f.head()

    pf = pd.DataFrame(d)
    pf = pf[pf['col1'] > 3]
    print(pf.head())
