#!/usr/bin/env bash
# Build a single-file Flatpak bundle from dist/Moss
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DIST="${ROOT}/dist"
FP="${ROOT}/packaging/flatpak"
WORKDIR="${DIST}/flatpak-build"
REPO="${DIST}/flatpak-repo"
VERSION="${VERSION:-0.2.2}"

test -x "${DIST}/Moss" || { echo "missing ${DIST}/Moss"; exit 1; }

rm -rf "${WORKDIR}" "${REPO}"
mkdir -p "${WORKDIR}"
cp "${DIST}/Moss" "${WORKDIR}/Moss"
cp "${ROOT}/packaging/linux/moss.png" "${WORKDIR}/moss.png"
# Flatpak-specific desktop id
sed 's|^Icon=.*|Icon=org.moss.Moss|; s|^Exec=.*|Exec=moss|' \
  "${ROOT}/packaging/linux/moss.desktop" > "${WORKDIR}/org.moss.Moss.desktop"
cp "${FP}/org.moss.Moss.yml" "${WORKDIR}/org.moss.Moss.yml"

flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo || true
flatpak install -y --user flathub org.freedesktop.Platform//24.08 org.freedesktop.Sdk//24.08 || true

flatpak-builder --user --force-clean --repo="${REPO}" "${WORKDIR}/build" "${WORKDIR}/org.moss.Moss.yml"
flatpak build-bundle "${REPO}" "${DIST}/Moss-x86_64.flatpak" org.moss.Moss
ls -lh "${DIST}/Moss-x86_64.flatpak"
