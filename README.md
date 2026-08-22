# Moss

**Native Linux / SteamOS launcher for Windows games.**

Proton and Wine prefixes. Missing-DLL fixes. Steam artwork. `setup.exe` installs.

Not Lutris. Not Electron. Not a Steam replacement.

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-7FAF82?style=flat-square&labelColor=191A19)](https://www.python.org/)
[![Qt Quick](https://img.shields.io/badge/UI-Qt%20Quick%20%2F%20QML-7C9BB8?style=flat-square&labelColor=191A19)](https://doc.qt.io/qt-6/qtquick-index.html)
[![Linux](https://img.shields.io/badge/platform-Linux%20%2F%20SteamOS-B4B8B3?style=flat-square&labelColor=191A19)](#)
[![Release](https://img.shields.io/badge/status-v0.2.9--pre-7FAF82?style=flat-square&labelColor=191A19)](https://github.com/LostSaki/Moss/releases)

---

## What it does

| | |
| --- | --- |
| **Scan library** | Point at a parent folder of Windows games; pick which titles to import |
| **Add one game** | Add a specific game folder or `.exe` without scanning siblings |
| **Prefix** | Creates a per-game Wine/Proton `pfx` |
| **Components** | Auto-installs winetricks verbs from defaults + a curated [games DB](docs/GAMES_DB.md) |
| **Artwork** | SteamGridDB / Steam CDN covers so Steam shortcuts are not blank |
| **Launch** | Runs under Proton (preferred) or Wine, with progress toasts |
| **Fix** | Log recipes + suggested fixes (AI advisor planned for a future 0.3.x) |
| **Updates** | Stable / Beta channels; portable builds can Install + Rollback in-app |
| **Support** | Error ring + export support pack for bug reports |

---

## Downloads

**Stable (latest full release):** [v0.2.2](https://github.com/LostSaki/Moss/releases/latest)

**Beta / pre-release:** [v0.2.9](https://github.com/LostSaki/Moss/releases) (and [v0.2.8](https://github.com/LostSaki/Moss/releases/tag/v0.2.8)) — set Settings → Updates → **Beta** to see these in-app.

### Linux

| Package | Notes |
| --- | --- |
| **`Moss-x86_64.AppImage`** | Recommended desktop / Steam Deck Desktop Mode — `chmod +x` then run |
| **`moss_*_amd64.deb`** | Debian / Ubuntu — `sudo apt install ./moss_*_amd64.deb` |
| **`Moss-x86_64.flatpak`** | `flatpak install --user Moss-x86_64.flatpak` (**network** permission required for update checks) |
| **`Moss-linux-x86_64`** | Portable binary — `chmod +x` then run |

### Steam Deck

1. Download the **AppImage** (or Flatpak) in Desktop Mode.
2. Mark executable and run once from Desktop Mode.
3. Optional Game Mode: Steam → Add Non-Steam Game → browse to the AppImage.
4. Steam/Proton (or Wine) + **winetricks** must be available for Windows titles and auto-components.

### Windows

| Package | Notes |
| --- | --- |
| **`Moss-Setup-*.exe`** | Installer (Start Menu + optional desktop shortcut) |
| **`Moss-windows-x86_64.exe`** | Portable UI preview |

Real Proton/Wine launches need Linux or SteamOS; Windows is for the UI shell and library management.

---

## Install from source (Linux / SteamOS)

```bash
pip install "git+https://github.com/LostSaki/Moss.git#egg=moss[ui]"
python -m moss ui
```

From a clone:

```bash
git clone https://github.com/LostSaki/Moss.git
cd Moss
pip install -e ".[ui,dev]"
python -m moss ui
```

### Host packages

- Python 3.11+
- Steam + Proton, or system Wine
- `winetricks` (and/or `protontricks`) — required for component auto-install
- Vulkan drivers (`vulkaninfo` should work)
- Optional: [SteamGridDB](https://www.steamgriddb.com/) API key

---

## CLI

```bash
moss scan ~/Games
moss scan --single ~/Games/SomeTitle
moss add ~/Games/SomeTitle/game.exe --name "Some Title"
moss install ~/Downloads/setup.exe --name "Some Title"
moss launch some-title
moss artwork some-title --search "Some Title"
moss config --steamgriddb-key YOUR_KEY --games-folder ~/Games
moss ui
```

On Windows, `moss` may not be on PATH — use `python -m moss …`.

---

## Local binary build

```powershell
pip install ".[ui]" pyinstaller
pyinstaller --noconfirm moss.spec
```

```bash
# Linux
pip install ".[ui]" pyinstaller
pyinstaller --noconfirm moss.spec
chmod +x dist/Moss
```

CI builds packages via **Actions → Build binaries** on `v*` tags.

---

## Data paths

| | Linux | Windows |
| --- | --- | --- |
| Data | `~/.local/share/moss/` | `%LOCALAPPDATA%\Moss` |
| Config | `~/.config/moss/config.json` | `%APPDATA%\Moss\config.json` |
| Prefixes | `…/moss/prefixes/<id>/pfx` | same under LocalAppData |
| Updates | `…/moss/updates/` (portable install / rollback) | same under LocalAppData |

---

## UI

Qt Quick (QML) with a dark botanical design system — restrained green accent, 1px borders, artwork-first library. Native OS title bar. **Scan library** sits above **Add Game** in the sidebar.

Settings → **Updates** (Stable / Beta), **Support** (diagnostics pack), **Runtimes** (Proton / Wine / Proton-GE).

---

## Auto-fix & suggestions

- Recipes: `src/moss/recipes.yaml`
- Games DB: `src/moss/data/games_db.yaml` — see [docs/GAMES_DB.md](docs/GAMES_DB.md)
- Launch failure → rule-based **Suggested fixes**
- Optional AI advisor is experimental and **not** a shipped 0.3.0 product release yet

---

## Release notes

See [CHANGELOG.md](CHANGELOG.md).

- **v0.2.9** (pre-release) — update-check reliability (SSL / GitHub API)
- **v0.2.8** (pre-release) — games DB, update channels, support packs
- **v0.2.2** — latest **Stable** full release (library scan UX + packages)

---

## License

MIT
