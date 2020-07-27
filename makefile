.PHONY: clean resources installer
clean:
	rm -r *.pyc dist build .pytest_cache

resources:
	pyside2-rcc data_preprocessor/resources.qrc -o data_preprocessor/qt_resources.py

installer: resources
	pyinstaller --name dataMole --onefile dataMole.spec main.py --clean