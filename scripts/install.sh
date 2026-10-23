#!/usr/bin/env bash
# Install the generated Catppuccin themes for Cinnamon.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${HOME}/.themes"

usage() {
  cat <<'EOF'
Usage: scripts/install.sh [--dest DIR]

Installs every dist/Catppuccin-* theme directory into DIR.
Defaults to ~/.themes (also read by Cinnamon).

After installation:
  1. Open Menu > Preferences > Themes (or System Settings > Themes).
  2. Pick Catppuccin Latte, Frappé, Macchiato or Mocha.
  3. Press Ctrl+Alt+Esc to restart Cinnamon if the change is not immediate.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dest)
      [[ $# -ge 2 ]] || { echo "missing value for --dest" >&2; exit 1; }
      DEST="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ ! -d "${ROOT}/dist" ]]; then
  echo "dist/ not found; run: python3 scripts/build.py" >&2
  exit 1
fi

mkdir -p "${DEST}"
count=0
for theme in "${ROOT}"/dist/Catppuccin-*/; do
  [[ -d "${theme}" ]] || continue
  name="$(basename "${theme}")"
  rm -rf "${DEST:?}/${name}"
  cp -R "${theme}" "${DEST}/${name}"
  echo "installed ${name} -> ${DEST}/${name}"
  count=$((count + 1))
done

if [[ ${count} -eq 0 ]]; then
  echo "no Catppuccin-* theme found in dist/; run: python3 scripts/build.py" >&2
  exit 1
fi

echo
echo "Themes installed in ${DEST}."
echo "Open Settings > Themes, choose a Catppuccin flavor, then press Ctrl+Alt+Esc."
