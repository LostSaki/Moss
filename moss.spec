# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules

pyside_datas, pyside_binaries, pyside_hidden = collect_all("PySide6")

a = Analysis(
    ["src/moss/__main__.py"],
    pathex=["src"],
    binaries=pyside_binaries,
    datas=[
        ("src/moss/recipes.yaml", "moss"),
        ("src/moss/data/games_db.yaml", "moss/data"),
        ("src/moss/ui/qml", "moss/ui/qml"),
        *pyside_datas,
    ],
    hiddenimports=collect_submodules("moss")
    + pyside_hidden
    + [
        "PySide6.QtQuick",
        "PySide6.QtQuickControls2",
        "PySide6.QtQml",
    ],
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
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)
