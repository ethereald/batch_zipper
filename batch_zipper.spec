# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Batch Zipper/Unzipper GUI
# Author: Kelvin
# Version: 1.0.0.0

block_cipher = None

import sys
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('zipper')

a = Analysis([
    'batch_zipper_gui.py',
],
    pathex=['.'],
    binaries=[],
    datas=[('batch_zipper_icon.ico', '.')],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BatchZipper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='batch_zipper_icon.ico',
    version='version.txt',
)