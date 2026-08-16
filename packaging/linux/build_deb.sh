#!/usr/bin/env bash
# Build moss_VERSION_amd64.deb from dist/Moss
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DIST="${ROOT}/dist"
VERSION="${VERSION:-0.2.2}"
STAGE="${DIST}/deb-stage"
NAME="moss_${VERSION}_amd64"

test -x "${DIST}/Moss" || { echo "missing ${DIST}/Moss"; exit 1; }
rm -rf "${STAGE}"
mkdir -p \
  "${STAGE}/DEBIAN" \
  "${STAGE}/usr/lib/moss" \
  "${STAGE}/usr/bin" \
  "${STAGE}/usr/share/applications" \
  "${STAGE}/usr/share/icons/hicolor/256x256/apps" \
  "${STAGE}/usr/share/doc/moss"

cp "${DIST}/Moss" "${STAGE}/usr/lib/moss/Moss"
chmod 755 "${STAGE}/usr/lib/moss/Moss"
ln -sf ../lib/moss/Moss "${STAGE}/usr/bin/moss"
cp "${ROOT}/packaging/linux/moss.desktop" "${STAGE}/usr/share/applications/moss.desktop"
sed -i 's|^Exec=.*|Exec=moss|' "${STAGE}/usr/share/applications/moss.desktop"
cp "${ROOT}/packaging/linux/moss.png" "${STAGE}/usr/share/icons/hicolor/256x256/apps/moss.png"
cp "${ROOT}/packaging/linux/moss.desktop" "${STAGE}/usr/share/applications/org.moss.Moss.desktop" 2>/dev/null || true

cat > "${STAGE}/DEBIAN/control" <<EOF
Package: moss
Version: ${VERSION}
Section: games
Priority: optional
Architecture: amd64
Maintainer: Moss <https://github.com/LostSaki/Moss>
Depends: libc6
Description: Native Linux/SteamOS launcher for Windows games
 Moss runs Windows games via Proton/Wine with per-game prefixes,
 artwork, and missing-DLL recipes. Host Steam/Proton or Wine recommended.
EOF

cat > "${STAGE}/usr/share/doc/moss/copyright" <<EOF
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: Moss
Source: https://github.com/LostSaki/Moss
Files: *
Copyright: Moss contributors
License: MIT
EOF

dpkg-deb --root-owner-group --build "${STAGE}" "${DIST}/${NAME}.deb"
ls -lh "${DIST}/${NAME}.deb"
