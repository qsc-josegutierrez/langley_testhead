# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for TestHead Control GUI

block_cipher = None

a = Analysis(
    ['testhead_gui.py', 'config_loader.py', 'testhead_control.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('config/*.xlsx', 'config'),  # Include all Excel config files
        ('config/*.json', 'config'),  # Include all JSON config files
        ('config_loader.py', '.'),     # Explicitly include config_loader
        ('testhead_control.py', '.'),  # Explicitly include testhead_control
        ('accesio/*.py', 'accesio'),   # Include accesio module
        # ('testhead_icon.ico', '.'),    # Include application icon (uncomment when icon exists)
    ],
    hiddenimports=['openpyxl', 'pandas', 'openpyxl.styles', 'openpyxl.cell', 'openpyxl.cell.cell'],
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
    name='testhead_gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window for GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Set to 'testhead_icon.ico' when icon file exists
)
