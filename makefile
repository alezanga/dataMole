.PHONY: clean resources installer
clean:
	find . -type d -name __pycache__ ! -path */venv/* -exec rm -rf {} \;

resources:
	pyside2-rcc dataMole/resources.qrc -o dataMole/qt_resources.py

installer: resources
	pyinstaller --name dataMole --onefile dataMole.spec main.py --clean