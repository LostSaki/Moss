# Changelog

## 0.2.8 (pre-release)

### Added
- Curated **games_db.yaml** (game names → required winetricks components) with auto-install on import/Play
- Expanded default components: `vcrun2019`, `vcrun2022`, `d3dcompiler_47`
- Progress toasts for prefix prep and component installs; clearer missing-winetricks message
- Update **Stable / Beta** channels; portable **Install update** + **Rollback**
- Settings → **Support**: error ring, export support pack, GitHub Issues link
- Rule-based launch suggestions + `SuggestContext` hooks for the 0.3.0 AI advisor
- Experimental AI toggle (endpoint/key) ready for 0.3.0
- Quieter wineboot; Change EXE hint when the picked binary looks like a launcher

### Fixed
- Silent winetricks failures no longer look like “nothing happened”
- Play with no Proton/Wine routes to Settings → Runtimes

## 0.2.2

- Scan library UX, multi/single folder import, AppImage/deb/Flatpak/Windows Setup packaging

## 0.2.1

- Settings update status; quiet shell motion

## 0.2.0

- Themes, glass, onboarding, runners, per-game launch tools
