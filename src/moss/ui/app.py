from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QPlainTextEdit,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from moss.install import add_from_exe, add_from_folder, install_setup
from moss.launch import launch_game
from moss.store import Game, load_config, load_library, save_config


def _load_qss() -> str:
    return files("moss.ui").joinpath("theme.qss").read_text(encoding="utf-8")


class MossWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Moss")
        self.resize(1100, 700)
        self._games: dict[str, Game] = {}

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        split = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(split)

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(240)
        s_layout = QVBoxLayout(sidebar)
        s_layout.setContentsMargins(12, 16, 12, 16)
        brand = QLabel("MOSS")
        brand.setObjectName("meta")
        s_layout.addWidget(brand)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search")
        self.search.textChanged.connect(self._filter)
        s_layout.addWidget(self.search)
        self.list = QListWidget()
        self.list.currentItemChanged.connect(self._on_select)
        s_layout.addWidget(self.list, 1)
        row = QHBoxLayout()
        add_btn = QPushButton("Add folder")
        add_btn.clicked.connect(self._add_folder)
        exe_btn = QPushButton("Add exe")
        exe_btn.clicked.connect(self._add_exe)
        setup_btn = QPushButton("Installer")
        setup_btn.clicked.connect(self._add_setup)
        row.addWidget(add_btn)
        row.addWidget(exe_btn)
        row.addWidget(setup_btn)
        s_layout.addLayout(row)
        settings = QPushButton("Settings")
        settings.clicked.connect(self._settings)
        s_layout.addWidget(settings)
        split.addWidget(sidebar)

        detail = QWidget()
        d = QVBoxLayout(detail)
        d.setContentsMargins(28, 24, 28, 24)
        d.setSpacing(12)
        self.cover = QLabel()
        self.cover.setMinimumHeight(280)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover.setStyleSheet("border: 1px solid #222; border-radius: 12px;")
        d.addWidget(self.cover, 1)
        self.title = QLabel("Select a game")
        self.title.setObjectName("title")
        d.addWidget(self.title)
        self.meta = QLabel("PFX  —")
        self.meta.setObjectName("meta")
        d.addWidget(self.meta)
        self.dots = QLabel("●  vcrun   ●  d3d")
        self.dots.setObjectName("statusOk")
        d.addWidget(self.dots)
        actions = QHBoxLayout()
        self.play = QPushButton("Play")
        self.play.setObjectName("play")
        self.play.clicked.connect(self._play)
        self.stop = QPushButton("Stop")
        self.stop.setObjectName("stop")
        self.stop.setEnabled(False)
        actions.addWidget(self.play)
        actions.addWidget(self.stop)
        actions.addStretch()
        log_btn = QPushButton("Log")
        log_btn.clicked.connect(self._toggle_log)
        actions.addWidget(log_btn)
        d.addLayout(actions)
        self.log = QPlainTextEdit()
        self.log.setVisible(False)
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(180)
        d.addWidget(self.log)
        split.addWidget(detail)
        split.setStretchFactor(1, 1)

        self.reload()

    def reload(self) -> None:
        self._games = load_library()
        self._filter(self.search.text())

    def _filter(self, text: str) -> None:
        self.list.clear()
        q = (text or "").lower()
        for g in self._games.values():
            if q and q not in g.name.lower() and q not in g.id:
                continue
            item = QListWidgetItem(g.name)
            item.setData(Qt.ItemDataRole.UserRole, g.id)
            self.list.addItem(item)

    def _current(self) -> Game | None:
        item = self.list.currentItem()
        if not item:
            return None
        return self._games.get(item.data(Qt.ItemDataRole.UserRole))

    def _on_select(self) -> None:
        g = self._current()
        if not g:
            return
        self.title.setText(g.name)
        self.meta.setText(f"PFX  {g.id}    {g.exe}")
        vcrun = "vcrun2019" in g.verbs
        d3d = "d3dcompiler_47" in g.verbs
        self.dots.setText(
            f"{'●' if vcrun else '○'}  vcrun2019    {'●' if d3d else '○'}  d3dcompiler_47"
        )
        self.dots.setObjectName("statusOk" if vcrun and d3d else "statusBad")
        art = g.artwork.get("hero") or g.artwork.get("grid")
        if art and Path(art).is_file():
            pix = QPixmap(art)
            self.cover.setPixmap(
                pix.scaled(640, 280, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )
        else:
            self.cover.setPixmap(QPixmap())
            letter = (g.name[:1] or "?").upper()
            self.cover.setText(letter)

    def _add_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Games folder")
        if path:
            add_from_folder(Path(path))
            self.reload()

    def _add_exe(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Windows executable", "", "Executables (*.exe)")
        if path:
            add_from_exe(Path(path))
            self.reload()

    def _add_setup(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Windows installer", "", "Executables (*.exe)")
        if not path:
            return
        name, ok = _prompt(self, "Game name")
        if ok and name:
            install_setup(Path(path), name)
            self.reload()

    def _settings(self) -> None:
        dlg = SettingsSheet(self)
        dlg.show()

    def _play(self) -> None:
        g = self._current()
        if not g:
            return
        result = launch_game(g)
        self.log.setPlainText((result.get("log") or "") + "\n" + "\n".join(result.get("tried") or []))
        self.log.setVisible(True)
        self.reload()

    def _toggle_log(self) -> None:
        self.log.setVisible(not self.log.isVisible())


def _prompt(parent: QWidget, title: str) -> tuple[str, bool]:
    from PySide6.QtWidgets import QInputDialog

    text, ok = QInputDialog.getText(parent, "Moss", title)
    return text, bool(ok)


class SettingsSheet(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle("Moss — Settings")
        self.resize(420, 220)
        cfg = load_config()
        form = QFormLayout(self)
        self.games = QLineEdit(cfg.get("games_folder", ""))
        self.key = QLineEdit(cfg.get("steamgriddb_api_key", ""))
        self.proton = QLineEdit(cfg.get("proton_path", ""))
        form.addRow("Games folder", self.games)
        form.addRow("SteamGridDB key", self.key)
        form.addRow("Proton path", self.proton)
        save = QPushButton("Save")
        save.setObjectName("play")
        save.clicked.connect(self._save)
        form.addRow(save)

    def _save(self) -> None:
        save_config(
            {
                "games_folder": self.games.text(),
                "steamgriddb_api_key": self.key.text(),
                "proton_path": self.proton.text(),
            }
        )
        self.close()


def run_app() -> int:
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("Moss")
    app.setStyleSheet(_load_qss())
    win = MossWindow()
    win.show()
    return app.exec()
