# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for TestHead Control executable

block_cipher = None

a = Analysis(
    ['testhead_control.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config/*.xlsx', 'config'),  # Include all Excel config files
        ('config/*.json', 'config'),  # Include all JSON config files
    ],
    hiddenimports=['openpyxl', 'pandas', 'accesio.accesio_dio'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='testhead_control',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one: 'icon.ico'
)
