#!/usr/bin/env bash
# Vérifications statiques dans une copie temporaire, sans modifier les livrables.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf -- "$WORK_DIR"' EXIT

cd "$ROOT"
bash -n scripts/check.sh scripts/install.sh
mkdir -p "$WORK_DIR/scripts"
cp scripts/build.py "$WORK_DIR/scripts/"
cp palette.json LICENSE "$WORK_DIR/"
cp -R src "$WORK_DIR/src"
PYTHONPYCACHEPREFIX="$WORK_DIR/pycache" python3 -m py_compile "$WORK_DIR/scripts/build.py"
python3 "$WORK_DIR/scripts/build.py"

python3 - "$WORK_DIR" <<'PY'
from pathlib import Path
import re
import sys
from zipfile import ZipFile

root = Path(sys.argv[1])
folders = [f"Catppuccin-{name}" for name in ("Latte", "Frappe", "Macchiato", "Mocha")]
for folder in folders:
    theme = root / "dist" / folder
    for relative in ("LICENSE", "index.theme", "cinnamon/cinnamon.css", "cinnamon/thumbnail.png"):
        if not (theme / relative).is_file():
            raise ValueError(f"Fichier manquant : {folder}/{relative}")
    css_path = theme / "cinnamon/cinnamon.css"
    for value in re.findall(r"url\(\s*([^)]*?)\s*\)", css_path.read_text()):
        asset = value.strip("\"'")
        if not (css_path.parent / asset).is_file():
            raise ValueError(f"Asset CSS manquant : {folder}/{asset}")

for name, members in [(folder, [folder]) for folder in folders] + [("Catppuccin-Cinnamon-all-flavors", folders)]:
    with ZipFile(root / "dist" / f"{name}.zip") as archive:
        if archive.testzip() is not None:
            raise ValueError(f"Archive corrompue : {name}")
        expected = {
            str(path.relative_to(root / "dist"))
            for folder in members
            for path in (root / "dist" / folder).rglob("*") if path.is_file()
        }
        if set(archive.namelist()) != expected:
            raise ValueError(f"Contenu incorrect : {name}")

print("Vérifications réussies : quatre thèmes, assets CSS et cinq archives.")
PY
