from __future__ import annotations

import json
import shlex
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

from moss import __version__
from moss.components import list_common_verbs, run_verb
from moss.debugreport import build_debug_report
from moss.install import (
    add_from_exe,
    add_single_game_folder,
    discover_games_in_library,
    import_discovered,
    install_setup,
)
from moss.launch import active_launch, apply_recipe_by_id, launch_game, stop_active_launch
from moss.paths import data_dir, logs_dir
from moss.prefix import apply_windows_version, backup_prefix, delete_prefix, open_prefix_path, prefix_info
from moss.runtime import (
    detect_runtime,
    install_proton_ge,
    list_runtimes,
    proton_ge_status,
    set_default_runtime,
)
from moss.store import WINDOWS_VERSIONS, delete_game, get_game, load_config, load_library, save_config, upsert
from moss.themes import AUTO_GLASS_THEMES, THEMES, list_themes, theme_tokens
from moss.updatecheck import REPO_URL, check_for_update
from moss.wrappers import host_tools_summary

def _file_url(path: str) -> str:
    if not path or not Path(path).is_file():
        return ""
    return QUrl.fromLocalFile(str(Path(path))).toString()


def _status(game) -> str:
    return "Ready" if game.is_ready() else "Needs Attention"


def _env_to_lines(env: dict) -> list[str]:
    return [f"{k}={v}" for k, v in sorted((env or {}).items())]


def _lines_to_env(lines) -> dict[str, str]:
    out: dict[str, str] = {}
    if not lines:
        return out
    for line in lines:
        text = str(line).strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, _, val = text.partition("=")
        key = key.strip()
        if key:
            out[key] = val.strip()
    return out


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
    finished_ok = Signal(str, bool, str, bool, str, str, bool, object, int)

    def __init__(self, game_id: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._game_id = game_id

    def run(self) -> None:
        game = get_game(self._game_id)
        if not game:
            self.finished_ok.emit(self._game_id, False, "Unknown game", False, "", "", False, None, 0)
            return
        result = launch_game(game)
        log = result.get("log") or ""
        tried = result.get("tried") or []
        if tried:
            log = "Tried: " + "; ".join(tried) + "\n\n" + log
        self.finished_ok.emit(
            self._game_id,
            bool(result.get("ok")),
            log,
            bool(result.get("anti_cheat")),
            str(result.get("message") or ""),
            str(result.get("recipe_id") or ""),
            bool(result.get("can_fix")),
            result.get("pid"),
            int(result.get("durationSec") or 0),
        )


class UpdateWorker(QThread):
    done = Signal(bool, str, str, str, str, bool)

    def run(self) -> None:
        info = check_for_update()
        self.done.emit(
            bool(info.available),
            str(info.current or __version__),
            str(info.latest or ""),
            str(info.message or ""),
            str(info.url or REPO_URL),
            bool(info.ok),
        )


class GeInstallWorker(QThread):
    done = Signal(bool, str)

    def run(self) -> None:
        result = install_proton_ge()
        self.done.emit(bool(result.get("ok")), str(result.get("message") or ""))


class LibraryScanWorker(QThread):
    done = Signal(object)  # list[dict]

    def __init__(self, path: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._path = path

    def run(self) -> None:
        found = discover_games_in_library(Path(self._path))
        self.done.emit([d.as_dict() for d in found])


class MossController(QObject):
    libraryChanged = Signal()
    toast = Signal(str)
    updateAvailable = Signal(str, str)
    updateStatusChanged = Signal()
    logReady = Signal(str)
    error = Signal(str)
    currentChanged = Signal()
    pageChanged = Signal()
    busyChanged = Signal()
    configChanged = Signal()
    themeChanged = Signal()
    glassChanged = Signal()
    runtimesChanged = Signal()
    onboardingChanged = Signal()
    antiCheatBlocked = Signal(str, str)
    launchFailed = Signal(str, str, bool, str, str)
    runningChanged = Signal()
    scanningChanged = Signal()
    discoveredGames = Signal("QVariant")

    def __init__(self, games: GameListModel, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._games = games
        self._page = "library"
        self._current: dict = {}
        self._busy = False
        self._running = False
        self._last_launch: dict = {}
        self._worker: LaunchWorker | None = None
        self._upd: UpdateWorker | None = None
        self._ge: GeInstallWorker | None = None
        self._checking_updates = False
        self._scanning = False
        self._scan: LibraryScanWorker | None = None
        self._last_update: dict = {
            "available": False,
            "current": __version__,
            "latest": "",
            "message": "",
            "url": REPO_URL,
            "ok": True,
        }
        self._cfg = load_config()
        self._tokens = theme_tokens(str(self._cfg.get("theme") or "moss_dark"))
        if self._cfg.get("check_updates", True):
            self.checkUpdatesNow()

    def _reload_cfg(self) -> None:
        self._cfg = load_config()
        self._tokens = theme_tokens(str(self._cfg.get("theme") or "moss_dark"))
        self.configChanged.emit()
        self.themeChanged.emit()
        self.glassChanged.emit()
        self.onboardingChanged.emit()

    def _on_update_done(
        self,
        available: bool,
        current: str,
        latest: str,
        message: str,
        url: str,
        ok: bool,
    ) -> None:
        self._checking_updates = False
        self._last_update = {
            "available": available,
            "current": current or __version__,
            "latest": latest,
            "message": message,
            "url": url or REPO_URL,
            "ok": ok,
        }
        self.updateStatusChanged.emit()
        if available and message:
            self.updateAvailable.emit(message, url)

    @Slot()
    def checkUpdatesNow(self) -> None:
        if self._checking_updates:
            return
        self._checking_updates = True
        self.updateStatusChanged.emit()
        self._upd = UpdateWorker(self)
        self._upd.done.connect(self._on_update_done)
        self._upd.start()

    @Property(str, notify=pageChanged)
    def page(self) -> str:
        return self._page

    @Property("QVariant", notify=currentChanged)
    def current(self) -> dict:
        return self._current

    @Property(bool, notify=busyChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(bool, notify=runningChanged)
    def running(self) -> bool:
        return self._running or bool(active_launch().get("running"))

    @Property("QVariant", notify=runningChanged)
    def launchMeta(self) -> dict:
        meta = dict(self._last_launch)
        meta.update(active_launch())
        return meta

    @Property(bool, notify=libraryChanged)
    def isEmpty(self) -> bool:
        return self._games.empty_library

    @Property(str, constant=True)
    def repoUrl(self) -> str:
        return REPO_URL

    @Property(str, constant=True)
    def version(self) -> str:
        return __version__

    @Property(str, constant=True)
    def dataDir(self) -> str:
        return str(data_dir())

    @Property("QVariant", notify=updateStatusChanged)
    def updateStatus(self) -> dict:
        return dict(self._last_update)

    @Property(bool, notify=updateStatusChanged)
    def checkingUpdates(self) -> bool:
        return self._checking_updates

    @Property(str, notify=themeChanged)
    def theme(self) -> str:
        return str(self._cfg.get("theme") or "moss_dark")

    @Property(bool, notify=glassChanged)
    def glassEnabled(self) -> bool:
        return bool(self._cfg.get("glass_enabled"))

    @Property("QVariant", notify=themeChanged)
    def themeTokens(self) -> dict:
        return dict(self._tokens)

    @Property(bool, notify=onboardingChanged)
    def onboardingComplete(self) -> bool:
        return bool(self._cfg.get("onboarding_complete"))

    @Property(bool, notify=scanningChanged)
    def scanningLibrary(self) -> bool:
        return self._scanning

    @Property(str, notify=configChanged)
    def gamesFolder(self) -> str:
        return str(self._cfg.get("games_folder") or "")

    @Property("QVariant", notify=configChanged)
    def themes(self) -> list:
        return list_themes()

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

    def _game_payload(self, g) -> dict:
        rt = detect_runtime(g)
        cover = _file_url(g.artwork.get("grid") or "")
        info = prefix_info(g.id)
        return {
            "gameId": g.id,
            "name": g.name,
            "cover": _file_url(g.artwork.get("hero") or g.artwork.get("grid") or "") or cover,
            "status": _status(g),
            "runtime": (rt.name if rt else "none"),
            "runtimeKind": (rt.kind if rt else "none"),
            "runnerId": g.runner_id or (rt.id if rt else ""),
            "prefix": g.prefix or info.get("path") or "",
            "prefixExists": bool(info.get("exists")),
            "canBackupPrefix": bool(info.get("canBackup")),
            "canDeletePrefix": bool(info.get("canDelete")),
            "exe": g.exe,
            "verbs": "  ".join(g.verbs) if g.verbs else "—",
            "lastPlayed": g.last_played or "—",
            "letter": (g.name[:1] or "M").upper(),
            "favorite": g.favorite,
            "workingDir": g.working_dir or "",
            "launchArgs": g.launch_args or "",
            "envVars": _env_to_lines(g.env_vars),
            "windowsVersion": g.windows_version or "",
            "dllOverrides": _env_to_lines(g.dll_overrides),
            "dxvkEnabled": bool(g.dxvk_enabled),
            "vkd3dEnabled": bool(g.vkd3d_enabled),
            "gamescopeEnabled": bool(g.gamescope_enabled),
            "mangohudEnabled": bool(g.mangohud_enabled),
            "gamemodeEnabled": bool(g.gamemode_enabled),
            "antiCheatHint": "",
        }

    @Slot(str)
    def openGame(self, game_id: str) -> None:
        g = get_game(game_id)
        if not g:
            return
        self._current = self._game_payload(g)
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
        self._running = True
        self.busyChanged.emit()
        self.runningChanged.emit()
        self._worker = LaunchWorker(game_id, self)
        self._worker.finished_ok.connect(self._play_done)
        self._worker.start()

    def _play_done(
        self,
        game_id: str,
        ok: bool,
        log: str,
        anti_cheat: bool = False,
        message: str = "",
        recipe_id: str = "",
        can_fix: bool = False,
        pid=None,
        duration: int = 0,
    ) -> None:
        self._busy = False
        self._running = False
        self.busyChanged.emit()
        self._last_launch = {
            "gameId": game_id,
            "ok": ok,
            "pid": pid,
            "durationSec": duration,
            "recipeId": recipe_id,
            "message": message,
        }
        self.runningChanged.emit()
        self._games.reload()
        self.libraryChanged.emit()
        self.openGame(game_id)
        if anti_cheat:
            hint = message or "This title uses unsupported anti-cheat under Proton/Wine."
            if self._current.get("gameId") == game_id:
                self._current = {**self._current, "antiCheatHint": hint}
                self.currentChanged.emit()
            self.logReady.emit(log)
            self.antiCheatBlocked.emit(hint, log)
            return
        if not ok:
            self.logReady.emit(log)
            title = "Launch failed"
            detail = message or "Moss could not identify a safe automatic fix."
            if can_fix and recipe_id:
                detail = f"{detail}\n\nRecommended fix available ({recipe_id})."
            self.launchFailed.emit(title, detail, can_fix, recipe_id, game_id)

    @Slot()
    def stop(self) -> None:
        result = stop_active_launch(force=False)
        self._running = False
        self.runningChanged.emit()
        self.toast.emit(str(result.get("message") or "Stopped"))

    @Slot(str, str)
    def applyRecommendedFix(self, game_id: str, recipe_id: str) -> None:
        g = get_game(game_id)
        if not g:
            self.toast.emit("Unknown game")
            return
        result = apply_recipe_by_id(g, recipe_id)
        self.toast.emit(str(result.get("message") or ("Done" if result.get("ok") else "Fix failed")))
        if result.get("ok"):
            self._games.reload()
            if self._current.get("gameId") == game_id:
                self.openGame(game_id)

    @Slot(str, result=str)
    def debugReport(self, game_id: str = "") -> str:
        return build_debug_report(game_id or "")

    @Slot(str)
    def copyDebugReport(self, game_id: str = "") -> None:
        from PySide6.QtGui import QGuiApplication

        text = build_debug_report(game_id or "")
        clip = QGuiApplication.clipboard()
        if clip:
            clip.setText(text)
            self.toast.emit("Debug report copied")
        else:
            self.toast.emit("Clipboard unavailable")

    def _set_games_folder(self, path: str) -> None:
        cfg = load_config()
        cfg["games_folder"] = path
        save_config(cfg)
        self._reload_cfg()

    def _on_scan_done(self, found) -> None:
        self._scanning = False
        self.scanningChanged.emit()
        rows = list(found or [])
        if not rows:
            self.toast.emit("No Windows games found in that folder")
            return
        if len(rows) == 1:
            games = import_discovered(rows)
            self._games.reload()
            self.libraryChanged.emit()
            if games:
                self.toast.emit(f"Added {games[0].name}")
            else:
                self.toast.emit("Already in your library")
            return
        self.discoveredGames.emit(rows)

    @Slot(str)
    def scanGamesFolder(self, path: str = "") -> None:
        """Multi-game library scan. Empty path uses saved games_folder."""
        if self._scanning:
            return
        folder = (path or "").strip() or str(self._cfg.get("games_folder") or "").strip()
        if not folder:
            self.toast.emit("Choose a games folder first")
            return
        root = Path(folder)
        if not root.is_dir():
            self.toast.emit("That games folder doesn't exist")
            return
        self._set_games_folder(str(root.resolve()))
        self._scanning = True
        self.scanningChanged.emit()
        self._scan = LibraryScanWorker(str(root.resolve()), self)
        self._scan.done.connect(self._on_scan_done)
        self._scan.start()

    @Slot(str)
    def addGameFolder(self, path: str) -> None:
        """Add exactly one game from a specific folder."""
        if not path:
            return
        game = add_single_game_folder(Path(path))
        self._games.reload()
        self.libraryChanged.emit()
        if game:
            self.toast.emit(f"Added {game.name}")
        else:
            self.toast.emit("No Windows game found in that folder")

    @Slot(str)
    def addFolder(self, path: str) -> None:
        # Back-compat: treat as specific game folder
        self.addGameFolder(path)

    @Slot(str)
    def importDiscovered(self, payload: str) -> None:
        """Import selected discover hits. payload is JSON list of {exe,name,...}."""
        try:
            items = json.loads(payload) if payload else []
        except json.JSONDecodeError:
            self.toast.emit("Couldn't import selection")
            return
        if not isinstance(items, list) or not items:
            self.toast.emit("Nothing selected")
            return
        games = import_discovered(items)
        self._games.reload()
        self.libraryChanged.emit()
        n = len(games)
        if n == 0:
            self.toast.emit("Those games are already in your library")
        elif n == 1:
            self.toast.emit(f"Added {games[0].name}")
        else:
            self.toast.emit(f"Added {n} games")

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

    @Slot(str)
    def openGamePrefix(self, game_id: str) -> None:
        path = open_prefix_path(game_id)
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    @Slot(str, result="QVariant")
    def prefixInfo(self, game_id: str):
        return prefix_info(game_id)

    @Slot(str)
    def backupGamePrefix(self, game_id: str) -> None:
        result = backup_prefix(game_id)
        self.toast.emit(str(result.get("message") or ("Backup done" if result.get("ok") else "Backup failed")))
        if self._current.get("gameId") == game_id:
            self.openGame(game_id)

    @Slot(str)
    def deleteGamePrefix(self, game_id: str) -> None:
        result = delete_prefix(game_id)
        self.toast.emit(str(result.get("message") or ("Deleted" if result.get("ok") else "Delete failed")))
        g = get_game(game_id)
        if g and result.get("ok"):
            g.prefix = str(open_prefix_path(game_id))
            upsert(g)
        if self._current.get("gameId") == game_id:
            self.openGame(game_id)

    @Slot()
    def openDataDir(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(data_dir())))

    @Slot()
    def openGithub(self) -> None:
        QDesktopServices.openUrl(QUrl(REPO_URL))

    @Slot(str)
    def openUrl(self, url: str) -> None:
        if url:
            QDesktopServices.openUrl(QUrl(url))

    @Slot(str)
    def loadLog(self, game_id: str) -> None:
        p = logs_dir() / f"{game_id}.log"
        text = p.read_text(encoding="utf-8", errors="replace") if p.exists() else "No log yet."
        self.logReady.emit(text)
        self._page = "logs"
        self.pageChanged.emit()

    @Slot(result="QVariant")
    def loadSettings(self):
        self._cfg = load_config()
        return dict(self._cfg)

    @Slot("QVariant")
    def saveSettings(self, data) -> None:
        cfg = load_config()
        if isinstance(data, dict):
            cfg.update({k: data[k] for k in data})
            save_config(cfg)
            self._reload_cfg()
            self.toast.emit("Settings saved")

    @Slot(str)
    def setTheme(self, theme_id: str) -> None:
        cfg = load_config()
        tid = theme_id if theme_id in THEMES else "moss_dark"
        cfg["theme"] = tid
        if tid in AUTO_GLASS_THEMES:
            cfg["glass_enabled"] = True
        save_config(cfg)
        self._reload_cfg()

    @Slot(bool)
    def setGlassEnabled(self, enabled: bool) -> None:
        cfg = load_config()
        cfg["glass_enabled"] = bool(enabled)
        save_config(cfg)
        self._reload_cfg()

    @Slot("QVariant")
    def completeOnboarding(self, data) -> None:
        cfg = load_config()
        if isinstance(data, dict):
            for key in (
                "games_folder",
                "preferred_runtime",
                "steamgriddb_api_key",
                "glass_enabled",
                "theme",
            ):
                if key in data:
                    cfg[key] = data[key]
        cfg["onboarding_complete"] = True
        save_config(cfg)
        self._reload_cfg()
        folder = str(cfg.get("games_folder") or "").strip()
        if folder and Path(folder).is_dir():
            self.toast.emit("Welcome to Moss — scanning your games folder")
            self.scanGamesFolder(folder)
        else:
            self.toast.emit("Welcome to Moss")

    @Slot(result="QVariant")
    def listRuntimes(self):
        return [rt.as_dict() for rt in list_runtimes()]

    @Slot(result="QVariant")
    def protonGeStatus(self):
        return proton_ge_status()

    @Slot(str)
    def setDefaultRuntime(self, runtime_id: str) -> None:
        result = set_default_runtime(runtime_id)
        if result:
            self._reload_cfg()
            self.runtimesChanged.emit()
            self.toast.emit(f"Default runtime: {result.get('name')}")
        else:
            self.toast.emit("Runtime not found")

    @Slot()
    def installProtonGE(self) -> None:
        if self._busy:
            return
        status = proton_ge_status()
        if not status.get("can_install"):
            self.toast.emit(status.get("message") or "Proton-GE install unavailable")
            return
        self._busy = True
        self.busyChanged.emit()
        self._ge = GeInstallWorker(self)
        self._ge.done.connect(self._ge_done)
        self._ge.start()

    def _ge_done(self, ok: bool, message: str) -> None:
        self._busy = False
        self.busyChanged.emit()
        self.runtimesChanged.emit()
        self._reload_cfg()
        self.toast.emit(message if message else ("Installed" if ok else "Install failed"))

    @Slot(str, result="QVariant")
    def getGameConfig(self, game_id: str):
        g = get_game(game_id)
        if not g:
            return {}
        rt = detect_runtime(g)
        return {
            "gameId": g.id,
            "name": g.name,
            "exe": g.exe,
            "workingDir": g.working_dir or "",
            "launchArgs": g.launch_args or "",
            "envVars": "\n".join(_env_to_lines(g.env_vars)),
            "favorite": g.favorite,
            "runnerId": g.runner_id or "",
            "resolvedRunnerId": (rt.id if rt else ""),
            "windowsVersion": g.windows_version or "",
            "dllOverrides": "\n".join(_env_to_lines(g.dll_overrides)),
            "windowsVersions": [v for v in WINDOWS_VERSIONS],
            "dxvkEnabled": bool(g.dxvk_enabled),
            "vkd3dEnabled": bool(g.vkd3d_enabled),
            "gamescopeEnabled": bool(g.gamescope_enabled),
            "gamescopeArgs": g.gamescope_args or "",
            "mangohudEnabled": bool(g.mangohud_enabled),
            "gamemodeEnabled": bool(g.gamemode_enabled),
            "esyncEnabled": bool(getattr(g, "esync_enabled", True)),
            "fsyncEnabled": bool(getattr(g, "fsync_enabled", True)),
            "launchProfiles": list(getattr(g, "launch_profiles", None) or []),
            "activeProfileId": str(getattr(g, "active_profile_id", "") or ""),
            "syncSupported": __import__("os").name == "posix",
        }

    @Slot("QVariant")
    def saveGameConfig(self, data) -> None:
        if not isinstance(data, dict):
            return
        game_id = str(data.get("gameId") or "")
        g = get_game(game_id)
        if not g:
            return
        if "name" in data and str(data["name"]).strip():
            g.name = str(data["name"]).strip()
        if "exe" in data and str(data["exe"]).strip():
            g.exe = str(data["exe"]).strip()
        if "workingDir" in data:
            g.working_dir = str(data.get("workingDir") or "").strip()
        if "launchArgs" in data:
            raw = str(data.get("launchArgs") or "")
            try:
                g.launch_args = " ".join(shlex.split(raw, posix=True)) if raw.strip() else ""
            except ValueError:
                g.launch_args = raw.strip()
        if "envVars" in data:
            env_raw = data.get("envVars")
            if isinstance(env_raw, list):
                g.env_vars = _lines_to_env(env_raw)
            else:
                g.env_vars = _lines_to_env(str(env_raw or "").splitlines())
        if "dllOverrides" in data:
            dll_raw = data.get("dllOverrides")
            if isinstance(dll_raw, list):
                g.dll_overrides = _lines_to_env(dll_raw)
            else:
                g.dll_overrides = _lines_to_env(str(dll_raw or "").splitlines())
        if "runnerId" in data:
            g.runner_id = str(data.get("runnerId") or "").strip()
        prev_win = g.windows_version
        if "windowsVersion" in data:
            win = str(data.get("windowsVersion") or "").strip()
            g.windows_version = win if win in WINDOWS_VERSIONS else ""
        if "favorite" in data:
            g.favorite = bool(data["favorite"])
        if "dxvkEnabled" in data:
            g.dxvk_enabled = bool(data["dxvkEnabled"])
        if "vkd3dEnabled" in data:
            g.vkd3d_enabled = bool(data["vkd3dEnabled"])
        if "gamescopeEnabled" in data:
            g.gamescope_enabled = bool(data["gamescopeEnabled"])
        if "gamescopeArgs" in data:
            g.gamescope_args = str(data.get("gamescopeArgs") or "").strip()
        if "mangohudEnabled" in data:
            g.mangohud_enabled = bool(data["mangohudEnabled"])
        if "gamemodeEnabled" in data:
            g.gamemode_enabled = bool(data["gamemodeEnabled"])
        if "esyncEnabled" in data:
            g.esync_enabled = bool(data["esyncEnabled"])
        if "fsyncEnabled" in data:
            g.fsync_enabled = bool(data["fsyncEnabled"])
        if "activeProfileId" in data:
            g.active_profile_id = str(data.get("activeProfileId") or "").strip()
        if "launchProfiles" in data and isinstance(data.get("launchProfiles"), list):
            cleaned = []
            for p in data["launchProfiles"]:
                if not isinstance(p, dict):
                    continue
                pid = str(p.get("id") or "").strip() or f"profile-{len(cleaned)+1}"
                cleaned.append(
                    {
                        "id": pid,
                        "name": str(p.get("name") or pid),
                        "launch_args": str(p.get("launch_args") or p.get("launchArgs") or ""),
                        "runner_id": str(p.get("runner_id") or p.get("runnerId") or ""),
                        "env_vars": dict(p.get("env_vars") or p.get("envVars") or {}),
                    }
                )
            g.launch_profiles = cleaned
        upsert(g)

        # Apply winecfg when Windows version changes
        if g.windows_version and g.windows_version != prev_win:
            rt = detect_runtime(g)
            if rt and Path(g.prefix).exists():
                result = apply_windows_version(rt, Path(g.prefix), g.windows_version)
                if result.get("message"):
                    self.toast.emit(str(result["message"]))

        self._games.reload()
        self.libraryChanged.emit()
        if self._current.get("gameId") == game_id:
            self.openGame(game_id)
        self.toast.emit("Game settings saved")

    @Slot(result="QVariant")
    def hostTools(self):
        return host_tools_summary()

    @Slot(str, result="QVariant")
    def listWinetricksVerbs(self, game_id: str):
        g = get_game(game_id)
        installed = list(g.verbs) if g else []
        return list_common_verbs(installed)

    @Slot(str, str)
    def runWinetricksVerb(self, game_id: str, verb: str) -> None:
        g = get_game(game_id)
        if not g or not verb:
            self.toast.emit("No game or verb selected")
            return
        rt = detect_runtime(g)
        if rt is None:
            self.toast.emit("No Proton/Wine runtime found")
            return
        prefix = Path(g.prefix)
        if not prefix.exists():
            from moss.prefix import create_prefix

            prefix = create_prefix(g.id, rt)
            g.prefix = str(prefix)
        ok = run_verb(rt, prefix, verb)
        if ok:
            if verb not in g.verbs:
                g.verbs.append(verb)
                upsert(g)
            self.toast.emit(f"Installed {verb}")
            self._games.reload()
            if self._current.get("gameId") == game_id:
                self.openGame(game_id)
        else:
            self.toast.emit(f"Failed to run winetricks {verb} (is winetricks installed?)")

    @Slot(str, result=str)
    def localPath(self, url: str) -> str:
        return QUrl(str(url)).toLocalFile()

    @Slot(str, result=str)
    def urlFromPath(self, path: str) -> str:
        if not path:
            return ""
        return QUrl.fromLocalFile(str(Path(path))).toString()
