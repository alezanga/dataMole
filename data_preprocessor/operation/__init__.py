import glob
import importlib.resources as res
import os
import xml.etree.ElementTree as eTree
from typing import Dict

# Dynamically load operation modules
modules = glob.glob(os.path.join(os.path.dirname(__file__), "*.py"))

__all__ = [os.path.basename(f)[:-3] for f in modules if
           os.path.isfile(f) and not f.endswith(('__init__.py', 'interface.py'))]

# Read operation description file
with res.path('data_preprocessor.resources', 'descriptions.html') as p:
    desc = str(p)
    tree = eTree.parse(desc)
    root = tree.getroot()

    # Take first element (which must be style) and put it inside every section
    style = list(root)[0]
    root.remove(style)
    for e in root:
        e.insert(0, style)

    descriptions: Dict[str, str] = {
        e.get('name'): eTree.tostring(e, encoding='unicode', method='xml').replace('\n', '')
            .replace('\t', '').replace('\r', '') for e in list(root)}
