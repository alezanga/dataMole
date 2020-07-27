# -*- mode: python ; coding: utf-8 -*-

# Add any package/module which is not imported explicitly, but its needed
hiddenimports = ['scipy.special.cython_special']
datas = []

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