# Changelog

## 0.2.2

### Added
- **Scan library** in the sidebar (above Add Game), Settings, empty library, and onboarding
- Multi-game library discovery with an Import dialog to pick which titles to add
- **Add this game folder…** for importing a single specific game without scanning siblings
- Linux packages: AppImage, `.deb`, Flatpak bundle, plus raw `Moss-linux-x86_64`
- Windows **Setup** installer (`Moss-Setup-0.2.2.exe`) alongside the portable exe
- Steam Deck / desktop install notes in the README
- GitHub Release notes and this changelog

### Fixed
- Saving a games folder no longer did nothing — Scan actually imports Windows `.exe` titles
- Honest feedback when a folder has zero suitable games (no fake “Games added”)

### Packaging
- CI builds and uploads AppImage, deb, Flatpak, Linux binary, Windows Setup, and portable exe on `v*` tags

## 0.2.1

- Settings update status (Check now / up-to-date / offline)
- Quiet shell motion (page fade, toast, dialogs, game cards)

## 0.2.0

- Themes, glass surfaces, onboarding, runners, per-game launch tools
