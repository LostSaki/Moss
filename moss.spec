# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

a = Analysis(
    ["src/moss/__main__.py"],
    pathex=["src"],
    binaries=[],
    datas=[
        ("src/moss/recipes.yaml", "moss"),
        ("src/moss/ui/qml", "moss/ui/qml"),
    ],
    hiddenimports=collect_submodules("moss"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Moss",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)
