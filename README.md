# dataMole

A Qt-based graphical tool to work with tabular datasets for machine learning projects

## Installation

1. Install Python >= 3.8.0
2. Open a terminal. On Windows 10 use the Windows PowerShell
3. Create a virtualenv:
    - Install virtualenv: `python -m pip install virtualenv`
    - Move in the main `dataMole` folder (the one with main.py)
    - Create a virtualenv: `python -m virtualenv venv`
    - Activate it: `source ./venv/bin/activate` (`.\venv\Scripts\Activate.ps1` on Windows)
4. Inside the virtualenv, install dependencies: `python -m pip install -r requirements.txt`
5. Generate Qt resources: `make resources` (*)
6. Start software with `python main.py`


(*) On Windows `make` command does not work, so the command to give at step 5 is: 

- `pyside2-rcc data_preprocessor/resources.qrc -o data_preprocessor/qt_resources.py`
