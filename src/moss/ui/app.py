from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from moss.ui.bridge import GameListModel, MossController


def qml_dir() -> Path:
    return Path(__file__).resolve().parent / "qml"


def run_app() -> int:
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    app.setApplicationName("Moss")
    games = GameListModel()
    controller = MossController(games)
    engine = QQmlApplicationEngine()
    app._moss_engine = engine
    app._moss_controller = controller
    app._moss_games = games
    engine.addImportPath(str(qml_dir()))
    engine.rootContext().setContextProperty("moss", controller)
    engine.rootContext().setContextProperty("games", games)
    engine.load(QUrl.fromLocalFile(str(qml_dir() / "Main.qml")))
    if not engine.rootObjects():
        return 1
    return app.exec()
