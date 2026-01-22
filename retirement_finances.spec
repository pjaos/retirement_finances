# -*- mode: python ; coding: utf-8 -*-
import os
import bcrypt
from PyInstaller.utils.hooks import collect_submodules
from nicegui import __path__ as nicegui_paths

nicegui_path = nicegui_paths[0]
block_cipher = None

# bcrypt .pyd
bcrypt_dir = os.path.dirname(bcrypt.__file__)
pyd_file = [f for f in os.listdir(bcrypt_dir) if f.startswith('_bcrypt') and f.endswith('.pyd')][0]
binaries = [(os.path.join(bcrypt_dir, pyd_file), "bcrypt")]

# NiceGUI must be added as data so .py files are included
datas = [
    ("src/retirement_finances", "retirement_finances"),
    ("src/retirement_finances/assets", "assets"),
    ("pyproject.toml", "assets"),
    (nicegui_path, 'nicegui'),
]

hidden_imports = []
hidden_imports += collect_submodules("p3lib")
hidden_imports += collect_submodules("plotly")
hidden_imports += collect_submodules("bcrypt")

a = Analysis(
    ['src/retirement_finances/retirement_finances.py'],
    pathex=['src'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=True,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='retirement_finances',
    debug=False,
    strip=False,
    upx=True,
    console=True,
    exclude_binaries=False,   # IMPORTANT for onefile
    bootloader_ignore_signals=False,
    onefile=True,             # <── THIS MAKES IT ONEFILE
)
