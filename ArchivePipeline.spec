# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['source/main.py'],
    pathex=['source'],
    binaries=[],
    datas=[('source/resources', 'resources')],
    hiddenimports=['PyQt6.QtCore','PyQt6.QtGui','PyQt6.QtWidgets','configparser','json','wand'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ArchivePipeline',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ArchivePipeline',
)
