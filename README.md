# Moss

**Native Linux / SteamOS launcher for Windows games.**

Proton and Wine prefixes. Missing-DLL fixes. Steam artwork. `setup.exe` installs.

Not Lutris. Not Electron. Not a Steam replacement.

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-7FAF82?style=flat-square&labelColor=191A19)](https://www.python.org/)
[![Qt Quick](https://img.shields.io/badge/UI-Qt%20Quick%20%2F%20QML-7C9BB8?style=flat-square&labelColor=191A19)](https://doc.qt.io/qt-6/qtquick-index.html)
[![Linux](https://img.shields.io/badge/platform-Linux%20%2F%20SteamOS-B4B8B3?style=flat-square&labelColor=191A19)](#)
[![Pre-release](https://img.shields.io/badge/status-v0.2.0--pre-D1A85A?style=flat-square&labelColor=191A19)](https://github.com/LostSaki/Moss/releases)

---

## What it does

| | |
| --- | --- |
| **Scan** | Point at a folder of Windows games; Moss finds the main `.exe` |
| **Prefix** | Creates a per-game Wine/Proton `pfx` |
| **Components** | Installs common winetricks verbs (`vcrun2019`, `d3dcompiler_47`) |
| **Artwork** | SteamGridDB / Steam CDN covers so Steam shortcuts are not blank |
| **Launch** | Runs under Proton (preferred) or Wine |
| **Fix** | Reads the debug log, matches recipes, retries up to 3 times |

---

## Install (Linux / SteamOS)

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
- `winetricks` (and/or `protontricks`)
- Vulkan drivers (`vulkaninfo` should work)
- Optional: [SteamGridDB](https://www.steamgriddb.com/) API key

---

## CLI

```bash
moss scan ~/Games
moss add ~/Games/SomeTitle/game.exe --name "Some Title"
moss install ~/Downloads/setup.exe --name "Some Title"
moss launch some-title
moss artwork some-title --search "Some Title"
moss config --steamgriddb-key YOUR_KEY --games-folder ~/Games
moss ui
```

On Windows, `moss` may not be on PATH — use `python -m moss …`.

---

## Windows note

You can open the **UI shell** and run unit tests on Windows. Real Proton/Wine launches need Linux or SteamOS.

Preview `.exe` (UI only):

```powershell
pip install pyinstaller
pyinstaller --noconfirm moss.spec
```

---

## Data paths

| | Linux | Windows |
| --- | --- | --- |
| Data | `~/.local/share/moss/` | `%LOCALAPPDATA%\Moss` |
| Config | `~/.config/moss/config.json` | `%APPDATA%\Moss\config.json` |
| Prefixes | `…/moss/prefixes/<id>/pfx` | same under LocalAppData |

---

## UI

Qt Quick (QML) with a dark botanical design system — restrained green accent, 1px borders, artwork-first library. Native OS title bar.

---

## Auto-fix

Recipes live in `src/moss/recipes.yaml`. Example: `VCRUNTIME140.dll` → `vcrun2019`. Unknown DLLs and Easy Anti-Cheat stop the loop and show the log.

---

## Pre-release

**v0.2.0-pre** is a pre-release: QML frontend and design system are new. Expect rough edges. Production Proton gameplay still targets Linux/SteamOS.

---

## License

MIT
