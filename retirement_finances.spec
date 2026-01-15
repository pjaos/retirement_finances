# -*- mode: python ; coding: utf-8 -*-
import os
import bcrypt
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Locate bcrypt compiled extension (.pyd file)
bcrypt_dir = os.path.dirname(bcrypt.__file__)
pyd_file = [f for f in os.listdir(bcrypt_dir) if f.startswith('_bcrypt') and f.endswith('.pyd')][0]
binaries = [(os.path.join(bcrypt_dir, pyd_file), "bcrypt")]

# Your assets folder (adjust if needed)
datas = [("assets", "assets"),
         ("pyproject.toml", "."),  # include pyproject.toml at the root of the bundled app
        ]

# Collect hidden imports for your dependencies
hidden_imports = []
hidden_imports += collect_submodules("p3lib")
hidden_imports += collect_submodules("nicegui")
hidden_imports += collect_submodules("plotly")
hidden_imports += collect_submodules("bcrypt")

a = Analysis(
    ['src/retirement_finances/retirement_finances.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=['.'],  # Add this line to tell PyInstaller where to find extra hooks
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
    name='retirement_finances',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Change to True for debugging console output
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    onefile=True,  # Onefile bundling enabled
)
