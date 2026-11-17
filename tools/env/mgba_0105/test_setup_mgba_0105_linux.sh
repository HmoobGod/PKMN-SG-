#!/usr/bin/env bash
# Offline source-only installer regression using a locally supplied AppImage.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "$0")" && pwd)"
BOOTSTRAP="$ROOT/setup_mgba_0105_linux.sh"
APPIMAGE="${1:-}"
[[ -n "$APPIMAGE" && -f "$APPIMAGE" ]] || { echo 'Usage: test_setup_mgba_0105_linux.sh /path/to/verified/AppImage' >&2; exit 2; }
APPIMAGE="$(realpath "$APPIMAGE")"
tmp=$(mktemp -d)
trap 'rm -rf -- "$tmp"' EXIT

assert() { "$@" || { echo "FAIL: $*" >&2; exit 1; }; }
assert bash "$BOOTSTRAP" --source "$APPIMAGE" --dest "$tmp/install"
assert test -f "$tmp/install/mGBA-0.10.5-appimage-x64.appimage"
assert test -x "$tmp/install/squashfs-root/usr/bin/mgba-qt"
assert bash "$BOOTSTRAP" --source "$APPIMAGE" --dest "$tmp/install"
# Corrupt a different copy: it must be refused before extraction or install.
cp -- "$APPIMAGE" "$tmp/tampered.appimage"
printf '\377' | dd of="$tmp/tampered.appimage" bs=1 seek=128 count=1 conv=notrunc status=none
if bash "$BOOTSTRAP" --source "$tmp/tampered.appimage" --dest "$tmp/rejected" >/dev/null 2>&1; then
  echo 'FAIL: tampered input was accepted' >&2; exit 1
fi
assert test ! -e "$tmp/rejected"
if bash "$BOOTSTRAP" --source "$APPIMAGE" --dest "$tmp/install/squashfs-root" >/dev/null 2>&1; then
  echo 'FAIL: existing destination was accepted' >&2; exit 1
fi
# Missing file or symlink source must not produce a directory.
if bash "$BOOTSTRAP" --source "$tmp/missing" --dest "$tmp/missing-install" >/dev/null 2>&1; then
  echo 'FAIL: missing source was accepted' >&2; exit 1
fi
assert test ! -e "$tmp/missing-install"
echo 'PASS: pinned local install, idempotence, version, corruption rejection, missing-source rejection'
