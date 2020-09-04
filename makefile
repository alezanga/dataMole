.PHONY: clean resources installer
clean:
    find . -type d -name __pycache__ ! -path */venv/* -exec rm -rf {} \;

resources:
	pyside2-rcc data_preprocessor/resources.qrc -o data_preprocessor/qt_resources.py

installer: resources
	pyinstaller --name dataMole --onefile dataMole.spec main.py --clean