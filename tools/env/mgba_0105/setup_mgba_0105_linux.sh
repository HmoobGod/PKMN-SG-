#!/usr/bin/env bash
# Install pinned, official mGBA 0.10.5 Linux x86_64 AppImage without touching game data.
# Emulator binary is never stored in this Git repository; install outside the worktree.
set -Eeuo pipefail
umask 077

readonly VERSION='0.10.5'
readonly APPIMAGE_NAME='mGBA-0.10.5-appimage-x64.appimage'
readonly EXPECTED_SHA256='fdf0a5c1588e1606c38315735cf48a9f9dca3573f32a3947ebc956f8297e85cd'
readonly OFFICIAL_URL="https://github.com/mgba-emu/mgba/releases/download/${VERSION}/${APPIMAGE_NAME}"

usage() {
  cat <<'EOF'
Usage: setup_mgba_0105_linux.sh [--source PATH] [--dest DIR]

No --source: fetch the mGBA 0.10.5 Linux x64 AppImage from mgba-emu/mgba's
official GitHub release. --source: use an existing local AppImage (e.g. the
owner's Google Drive backup) instead of downloading.

The expected SHA256 is pinned from the owner's previously recovered 25,208,000
byte mGBA 0.10.5 Linux AppImage. Both sources must match exactly or installation
fails closed. Install defaults to an XDG cache directory OUTSIDE the repository.
No ROM, SAV, savestate or private test artifact is ever read or uploaded.
EOF
}

source_file=''
dest="${XDG_CACHE_HOME:-${HOME}/.cache}/pokemon-soulgold/mgba/${VERSION}"
while (($#)); do
  case "$1" in
    --source) (($# >= 2)) || { echo 'Missing --source value' >&2; exit 2; }; source_file="$2"; shift 2 ;;
    --dest)   (($# >= 2)) || { echo 'Missing --dest value' >&2; exit 2; }; dest="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

[[ $(uname -s) == Linux && $(uname -m) == x86_64 ]] || { echo 'Requires Linux x86_64' >&2; exit 2; }
command -v sha256sum >/dev/null || { echo 'sha256sum required' >&2; exit 2; }
command -v mktemp >/dev/null || { echo 'mktemp required' >&2; exit 2; }
command -v realpath >/dev/null || { echo 'realpath required' >&2; exit 2; }

if [[ -n "$source_file" ]]; then
  [[ -f "$source_file" && ! -L "$source_file" ]] || { echo 'Local source missing or symlink' >&2; exit 2; }
  source_file=$(realpath -- "$source_file")
else
  command -v curl >/dev/null || { echo 'curl required for official release download' >&2; exit 2; }
fi

# The target must not alias a game input, point through a symlink, or live inside
# the current Git worktree. Installation only creates this dedicated directory.
[[ -n "$dest" && "$dest" != '/' && "$dest" != '.' ]] || { echo 'Unsafe destination' >&2; exit 2; }
if [[ -e "$dest" || -L "$dest" ]]; then
  [[ -d "$dest" && ! -L "$dest" ]] || { echo 'Destination is not a directory or is symlinked' >&2; exit 2; }
fi
mkdir -p -- "$(dirname -- "$dest")"
parent=$(realpath -- "$(dirname -- "$dest")")
dest="$parent/$(basename -- "$dest")"
if command -v git >/dev/null 2>&1; then
  if git -C "$parent" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo 'Refusing to place emulator inside a Git worktree' >&2; exit 2
  fi
fi

verify() {
  local path="$1" got
  [[ -f "$path" && ! -L "$path" ]] || return 1
  got=$(sha256sum -- "$path")
  [[ "${got%% *}" == "$EXPECTED_SHA256" ]] || { echo 'mGBA SHA256 mismatch; rejecting binary' >&2; return 1; }
  [[ "$(wc -c < "$path" | tr -d ' ')" == 25208000 ]] || { echo 'mGBA size mismatch; rejecting binary' >&2; return 1; }
}

if [[ -d "$dest" ]]; then
  # Idempotence is allowed only for an already-valid installation.
  verify "$dest/$APPIMAGE_NAME" || { echo 'Existing install invalid; refusing overwrite' >&2; exit 1; }
  [[ -x "$dest/squashfs-root/usr/bin/mgba-qt" ]] || { echo 'Existing installation incomplete' >&2; exit 1; }
  version_output=$("$dest/squashfs-root/usr/bin/mgba-qt" --version)
  [[ "$version_output" == *'mgba-qt 0.10.5'* ]] || { echo 'Existing runtime version mismatch' >&2; exit 1; }
  echo "READY: $dest/squashfs-root/usr/bin/mgba-qt"
  exit 0
fi

stage=$(mktemp -d -- "$parent/.mgba-0.10.5-stage.XXXXXXXX")
cleanup() { [[ -z "${stage:-}" ]] || rm -rf -- "$stage"; }
trap cleanup EXIT HUP INT TERM
out="$stage/$APPIMAGE_NAME"
if [[ -n "$source_file" ]]; then
  cp -- "$source_file" "$out"
else
  curl --fail --location --proto '=https' --tlsv1.2 --retry 2 --connect-timeout 15 --max-time 180 \
    --output "$out" "$OFFICIAL_URL"
fi
verify "$out" || exit 1
chmod 700 -- "$out"
(
  cd -- "$stage"
  "./$APPIMAGE_NAME" --appimage-extract >/dev/null
)
[[ -x "$stage/squashfs-root/usr/bin/mgba-qt" ]] || { echo 'AppImage extraction failed' >&2; exit 1; }
version_output=$("$stage/squashfs-root/usr/bin/mgba-qt" --version)
[[ "$version_output" == *'mgba-qt 0.10.5'* ]] || { echo "Wrong runtime version: $version_output" >&2; exit 1; }
# Only publish after the checksum, extraction and version checks all pass.
# This is an atomic directory rename on the same filesystem and refuses to replace.
[[ ! -e "$dest" && ! -L "$dest" ]] || { echo 'Destination appeared concurrently; refusing overwrite' >&2; exit 1; }
mv -T --no-clobber -- "$stage" "$dest"
[[ ! -e "$stage" && -d "$dest" ]] || { echo "Atomic installation was skipped; refusing apparent success" >&2; exit 1; }
verify "$dest/$APPIMAGE_NAME" || { echo "Post-install hash verification failed" >&2; exit 1; }
stage=''
echo "READY: $dest/squashfs-root/usr/bin/mgba-qt"
