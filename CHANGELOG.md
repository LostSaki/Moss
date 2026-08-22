# Changelog

## 0.2.9 (pre-release)

### Fixed
- Update check: GitHub Accept headers, **certifi** SSL for frozen/AppImage builds, clearer error text
- Stable channel: fall back when `/releases/latest` 404s (only prereleases published); guide users to **Beta**

## 0.2.8 (pre-release)

### Added
- Curated **games_db.yaml** with auto-install on import/Play
- Expanded default components: `vcrun2019`, `vcrun2022`, `d3dcompiler_47`
- Progress toasts; clearer missing-winetricks message
- Update **Stable / Beta** channels; portable **Install update** + **Rollback**
- Settings → **Support**: error ring, export support pack, GitHub Issues link
- Rule-based launch suggestions + `SuggestContext` hooks (AI advisor planned for a future **0.3.x**)
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

## Unreleased / future (0.3.x)

- Opt-in AI log advisor (code hooks exist; not a shipped product release yet)
