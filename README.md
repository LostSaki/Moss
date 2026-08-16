# Moss

Native Linux/SteamOS app for Windows games: Proton/Wine prefixes, missing-DLL fixes, Steam artwork, and setup.exe installs.

Moss is a standalone launcher (not a Lutris plugin). It scans a games folder or runs a Windows `setup.exe` in a prefix (`pfx`), installs common winetricks verbs, writes desktop and Steam shortcuts with artwork, then launches under Proton or Wine. If the debug log matches a known error, it applies one fix and retries (max 3).

## Host (Linux / SteamOS)

- Python 3.11+
- Steam + Proton, or system Wine
- `winetricks` (and/or `protontricks`)
- Vulkan drivers (`vulkaninfo` should work)
- Optional: SteamGridDB API key for grid/hero/logo/icon art

Proton and Wine are not available in a useful way on Windows. You can run unit tests and open the UI shell there; real launches need a Deck, Linux box, or VM.

## Install

```bash
pip install -e ".[ui,dev]"
```

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

Data: `~/.local/share/moss/`  
Config: `~/.config/moss/config.json`  
Prefixes: `~/.local/share/moss/prefixes/<id>/pfx`

## Auto-fix

Recipes live in `src/moss/recipes.yaml`. Example: `VCRUNTIME140.dll` → `vcrun2019`. Unknown DLLs and Easy Anti-Cheat stop the loop and show the log.

## UI

Native Qt (PySide6). Black surface, green Play, purple Stop/errors. No browser engine.
