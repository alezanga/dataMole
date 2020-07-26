# -*- mode: python ; coding: utf-8 -*-

import importlib
import os

# List here all non code packages which should be imported
package_imports = ['data_preprocessor.resources', 'data_preprocessor.resources.icons']
datas = []
for package in package_imports:
    absPath = importlib.import_module(package).__path__[0]
    relPath = os.path.relpath(absPath)
    files = [f for f in os.listdir(absPath) if os.path.isfile(os.path.join(absPath, f)) and f != '__init__.py']
    datas.extend((os.path.join(absPath, f), relPath) for f in files)

# Add any package/module which is not imported explicitly, but its needed
hiddenimports = ['data_preprocessor.resources', 'scipy.special.cython_special']

block_cipher = None
a = Analysis(['main.py'],
             pathex=['/home/alessandro/uni/Tesi/data_preprocessor'],
             binaries=[],
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='dataMole',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True)