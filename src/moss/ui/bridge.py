from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    Property,
    QAbstractListModel,
    QModelIndex,
    QObject,
    Qt,
    QThread,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QDesktopServices

from moss.install import add_from_exe, add_from_folder, install_setup
from moss.launch import launch_game
from moss.paths import data_dir, logs_dir
from moss.runtime import detect_runtime
from moss.store import delete_game, get_game, load_config, load_library, save_config, upsert
from moss.updatecheck import REPO_URL, check_for_update


def _file_url(path: str) -> str:
    if not path or not Path(path).is_file():
        return ""
    return QUrl.fromLocalFile(str(Path(path))).toString()


def _status(game) -> str:
    return "Ready" if game.is_ready() else "Needs Attention"


class GameListModel(QAbstractListModel):
    GameIdRole = Qt.ItemDataRole.UserRole + 1
    NameRole = Qt.ItemDataRole.UserRole + 2
    CoverRole = Qt.ItemDataRole.UserRole + 3
    HeroRole = Qt.ItemDataRole.UserRole + 4
    StatusRole = Qt.ItemDataRole.UserRole + 5
    FavoriteRole = Qt.ItemDataRole.UserRole + 6
    LastPlayedRole = Qt.ItemDataRole.UserRole + 7
    RuntimeRole = Qt.ItemDataRole.UserRole + 8
    PrefixRole = Qt.ItemDataRole.UserRole + 9
    ExeRole = Qt.ItemDataRole.UserRole + 10
    VerbsRole = Qt.ItemDataRole.UserRole + 11
    LetterRole = Qt.ItemDataRole.UserRole + 12

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._all: list = []
        self._rows: list = []
        self._filter = "all"
        self._search = ""
        self.reload()

    def roleNames(self) -> dict:
        return {
            self.GameIdRole: b"gameId",
            self.NameRole: b"name",
            self.CoverRole: b"cover",
            self.HeroRole: b"hero",
            self.StatusRole: b"status",
            self.FavoriteRole: b"favorite",
            self.LastPlayedRole: b"lastPlayed",
            self.RuntimeRole: b"runtime",
            self.PrefixRole: b"prefix",
            self.ExeRole: b"exe",
            self.VerbsRole: b"verbs",
            self.LetterRole: b"letter",
        }

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: ARG002
        return len(self._rows)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._rows)):
            return None
        g = self._rows[index.row()]
        cover = _file_url(g.artwork.get("grid") or g.artwork.get("icon") or "")
        hero = _file_url(g.artwork.get("hero") or g.artwork.get("grid") or "")
        rt = detect_runtime()
        mapping = {
            self.GameIdRole: g.id,
            self.NameRole: g.name,
            self.CoverRole: cover,
            self.HeroRole: hero,
            self.StatusRole: _status(g),
            self.FavoriteRole: g.favorite,
            self.LastPlayedRole: g.last_played,
            self.RuntimeRole: rt.kind if rt else "none",
            self.PrefixRole: g.prefix,
            self.ExeRole: g.exe,
            self.VerbsRole: "  ".join(g.verbs) if g.verbs else "—",
            self.LetterRole: (g.name[:1] or "M").upper(),
        }
        return mapping.get(role)

    def reload(self) -> None:
        self.beginResetModel()
        self._all = list(load_library().values())
        self._apply()
        self.endResetModel()

    def _apply(self) -> None:
        rows = list(self._all)
        q = self._search.lower().strip()
        if q:
            rows = [g for g in rows if q in g.name.lower() or q in g.id]
        if self._filter == "favorites":
            rows = [g for g in rows if g.favorite]
        elif self._filter == "recent":
            rows = [g for g in rows if g.last_played]
            rows.sort(key=lambda g: g.last_played, reverse=True)
        elif self._filter == "installed":
            rows = [g for g in rows if Path(g.prefix).exists()]
        elif self._filter == "attention":
            rows = [g for g in rows if not g.is_ready()]
        else:
            rows.sort(key=lambda g: g.name.lower())
        self._rows = rows

    def set_filter(self, key: str) -> None:
        self._filter = key
        self.beginResetModel()
        self._apply()
        self.endResetModel()

    def set_search(self, text: str) -> None:
        self._search = text
        self.beginResetModel()
        self._apply()
        self.endResetModel()

    @property
    def empty_library(self) -> bool:
        return not self._all


class LaunchWorker(QThread):
    finished_ok = Signal(str, bool, str)

    def __init__(self, game_id: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._game_id = game_id

    def run(self) -> None:
        game = get_game(self._game_id)
        if not game:
            self.finished_ok.emit(self._game_id, False, "Unknown game")
            return
        result = launch_game(game)
        log = result.get("log") or ""
        tried = result.get("tried") or []
        if tried:
            log = "Tried: " + "; ".join(tried) + "\n\n" + log
        self.finished_ok.emit(self._game_id, bool(result.get("ok")), log)


class UpdateWorker(QThread):
    done = Signal(bool, str, str)

    def run(self) -> None:
        info = check_for_update()
        self.done.emit(info.available, info.message, info.url)


class MossController(QObject):
    libraryChanged = Signal()
    toast = Signal(str)
    updateAvailable = Signal(str, str)
    logReady = Signal(str)
    error = Signal(str)
    currentChanged = Signal()
    pageChanged = Signal()
    busyChanged = Signal()

    def __init__(self, games: GameListModel, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._games = games
        self._page = "library"
        self._current: dict = {}
        self._busy = False
        self._worker: LaunchWorker | None = None
        self._upd: UpdateWorker | None = None
        if load_config().get("check_updates", True):
            self._upd = UpdateWorker(self)
            self._upd.done.connect(self._on_update)
            self._upd.start()

    def _on_update(self, available: bool, message: str, url: str) -> None:
        if available:
            self.updateAvailable.emit(message, url)

    @Property(str, notify=pageChanged)
    def page(self) -> str:
        return self._page

    @Property("QVariant", notify=currentChanged)
    def current(self) -> dict:
        return self._current

    @Property(bool, notify=busyChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(bool, notify=libraryChanged)
    def isEmpty(self) -> bool:
        return self._games.empty_library

    @Property(str, constant=True)
    def repoUrl(self) -> str:
        return REPO_URL

    @Property(str, constant=True)
    def dataDir(self) -> str:
        return str(data_dir())

    @Slot(str)
    def setFilter(self, key: str) -> None:
        if key == "settings":
            self._page = "settings"
            self.pageChanged.emit()
            return
        self._page = "library"
        self._games.set_filter(key)
        self.pageChanged.emit()
        self.libraryChanged.emit()

    @Slot(str)
    def setSearch(self, text: str) -> None:
        self._games.set_search(text)
        self.libraryChanged.emit()

    @Slot(str)
    def openGame(self, game_id: str) -> None:
        g = get_game(game_id)
        if not g:
            return
        rt = detect_runtime()
        cover = _file_url(g.artwork.get("grid") or "")
        self._current = {
            "gameId": g.id,
            "name": g.name,
            "cover": _file_url(g.artwork.get("hero") or g.artwork.get("grid") or "") or cover,
            "status": _status(g),
            "runtime": (rt.kind if rt else "none"),
            "prefix": g.prefix,
            "exe": g.exe,
            "verbs": "  ".join(g.verbs) if g.verbs else "—",
            "lastPlayed": g.last_played or "—",
            "letter": (g.name[:1] or "M").upper(),
            "favorite": g.favorite,
        }
        self._page = "game"
        self.currentChanged.emit()
        self.pageChanged.emit()

    @Slot()
    def backToLibrary(self) -> None:
        self._page = "library"
        self.pageChanged.emit()

    @Slot(str)
    def play(self, game_id: str) -> None:
        if self._busy:
            return
        self._busy = True
        self.busyChanged.emit()
        self._worker = LaunchWorker(game_id, self)
        self._worker.finished_ok.connect(self._play_done)
        self._worker.start()

    def _play_done(self, game_id: str, ok: bool, log: str) -> None:
        self._busy = False
        self.busyChanged.emit()
        self._games.reload()
        self.libraryChanged.emit()
        self.openGame(game_id)
        if not ok:
            self.logReady.emit(log)
            self.error.emit("Launch finished with errors")

    @Slot(str)
    def addFolder(self, path: str) -> None:
        if not path:
            return
        add_from_folder(Path(path))
        self._games.reload()
        self.libraryChanged.emit()
        self.toast.emit("Games added")

    @Slot(str)
    def addExe(self, path: str) -> None:
        if not path:
            return
        add_from_exe(Path(path))
        self._games.reload()
        self.libraryChanged.emit()
        self.toast.emit("Game added")

    @Slot(str, str)
    def installSetup(self, path: str, name: str) -> None:
        if not path or not name:
            return
        install_setup(Path(path), name)
        self._games.reload()
        self.libraryChanged.emit()
        self.toast.emit("Installer finished")

    @Slot(str)
    def toggleFavorite(self, game_id: str) -> None:
        g = get_game(game_id)
        if not g:
            return
        g.favorite = not g.favorite
        upsert(g)
        self._games.reload()
        self.openGame(game_id)
        self.libraryChanged.emit()

    @Slot(str, bool)
    def removeGame(self, game_id: str, remove_prefix: bool) -> None:
        delete_game(game_id, remove_prefix=remove_prefix)
        self._games.reload()
        self.libraryChanged.emit()
        self.backToLibrary()

    @Slot(str)
    def openPrefix(self, path: str) -> None:
        if path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    @Slot()
    def openDataDir(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(data_dir())))

    @Slot()
    def openGithub(self) -> None:
        QDesktopServices.openUrl(QUrl(REPO_URL))

    @Slot(str)
    def loadLog(self, game_id: str) -> None:
        p = logs_dir() / f"{game_id}.log"
        text = p.read_text(encoding="utf-8", errors="replace") if p.exists() else "No log yet."
        self.logReady.emit(text)
        self._page = "logs"
        self.pageChanged.emit()

    @Slot("QVariant")
    def saveSettings(self, data) -> None:
        cfg = load_config()
        if isinstance(data, dict):
            cfg.update({k: data[k] for k in data})
            save_config(cfg)
            self.toast.emit("Settings saved")

    @Slot(str, result=str)
    def localPath(self, url: str) -> str:
        return QUrl(str(url)).toLocalFile()
