import html
import json
import xml.etree.ElementTree as eTree
from typing import Dict

# 1 - Read operation description file
from PySide2.QtCore import QFile

# noinspection PyUnresolvedReferences
from dataMole import qt_resources

descFile = QFile(':/resources/descriptions.html')
descFile.open(QFile.ReadOnly)
fileStr: str = str(descFile.readAll(), encoding='utf-8')
parsedStr = html.unescape(fileStr)
root = eTree.fromstring(parsedStr)
descFile.close()

# Take first element (which must be style) and put it inside every section
style = list(root)[0]
root.remove(style)
for e in root:
    e.insert(0, style)

descriptions: Dict[str, str] = {
    e.get('name'): eTree.tostring(e, encoding='unicode', method='xml').replace('\n', '')
        .replace('\t', '').replace('\r', '') for e in list(root)}

# 2 - Read operation modules (only names)
with open('dataMole/config/operations.json', 'r') as config:
    d = json.load(config)
    __all_modules__ = d['modules']
