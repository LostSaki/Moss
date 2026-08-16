#!/usr/bin/env bash
# Build Moss-x86_64.AppImage from dist/Moss (PyInstaller one-file).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DIST="${ROOT}/dist"
APPDIR="${DIST}/AppDir"
VERSION="${VERSION:-0.2.2}"

test -x "${DIST}/Moss" || { echo "missing ${DIST}/Moss"; exit 1; }
rm -rf "${APPDIR}"
mkdir -p \
  "${APPDIR}/usr/bin" \
  "${APPDIR}/usr/share/applications" \
  "${APPDIR}/usr/share/icons/hicolor/256x256/apps"

cp "${DIST}/Moss" "${APPDIR}/usr/bin/moss"
chmod +x "${APPDIR}/usr/bin/moss"
cp "${ROOT}/packaging/linux/moss.desktop" "${APPDIR}/moss.desktop"
sed -i 's|^Exec=.*|Exec=moss|' "${APPDIR}/moss.desktop"
cp "${APPDIR}/moss.desktop" "${APPDIR}/usr/share/applications/moss.desktop"
cp "${ROOT}/packaging/linux/moss.png" "${APPDIR}/moss.png"
cp "${ROOT}/packaging/linux/moss.png" "${APPDIR}/usr/share/icons/hicolor/256x256/apps/moss.png"

cd "${DIST}"
curl -fsSL -o linuxdeploy.AppImage \
  https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
curl -fsSL -o appimagetool.AppImage \
  https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x linuxdeploy.AppImage appimagetool.AppImage

rm -rf linuxdeploy-extract appimagetool-extract
./linuxdeploy.AppImage --appimage-extract
mv squashfs-root linuxdeploy-extract
./appimagetool.AppImage --appimage-extract
mv squashfs-root appimagetool-extract

./linuxdeploy-extract/AppRun --appdir "${APPDIR}" \
  --executable "${APPDIR}/usr/bin/moss" \
  --desktop-file "${APPDIR}/moss.desktop" \
  --icon-file "${APPDIR}/moss.png"

ARCH=x86_64 ./appimagetool-extract/AppRun "${APPDIR}" "${DIST}/Moss-x86_64.AppImage"
chmod +x "${DIST}/Moss-x86_64.AppImage"
ls -lh "${DIST}/Moss-x86_64.AppImage"
