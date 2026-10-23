#!/usr/bin/env bash
# Vérifications statiques dans une copie temporaire, sans modifier les livrables.
# Compare aussi dist/ et previews/ suivis à une compilation fraîche : une
# modification des gabarits sans reconstruction fait échouer le script.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf -- "$WORK_DIR"' EXIT

cd "$ROOT"
bash -n scripts/check.sh scripts/install.sh
mkdir -p "$WORK_DIR/scripts"
cp scripts/build.py scripts/test_build.py scripts/install.sh "$WORK_DIR/scripts/"
cp palette.json LICENSE "$WORK_DIR/"
cp -R src "$WORK_DIR/src"
PYTHONPYCACHEPREFIX="$WORK_DIR/pycache" python3 -m py_compile \
  "$WORK_DIR/scripts/build.py" "$WORK_DIR/scripts/test_build.py"

echo "Tests unitaires de build.py :"
PYTHONPYCACHEPREFIX="$WORK_DIR/pycache" python3 "$WORK_DIR/scripts/test_build.py"

python3 "$WORK_DIR/scripts/build.py"

compare_tree() {
  local name="$1"
  local expected="$ROOT/$name"
  if [[ ! -d "$expected" ]]; then
    echo "  $name/ absent du dépôt : comparaison ignorée (lancer python3 scripts/build.py)." >&2
    return 0
  fi
  if ! diff -rq "$expected" "$WORK_DIR/$name"; then
    echo "error: $name/ ne correspond pas à une compilation fraîche." >&2
    echo "       relancer python3 scripts/build.py (accent par défaut) puis valider les fichiers modifiés." >&2
    return 1
  fi
  echo "  $name/ identique à la compilation fraîche."
}

check_installer() {
  local install_dir="$WORK_DIR/installed"
  local folder
  echo "Vérification de scripts/install.sh :"

  bash "$WORK_DIR/scripts/install.sh" --dry-run --dest "$install_dir" >"$WORK_DIR/install-dry-run.log"
  if [[ -e "$install_dir" ]]; then
    echo "error: --dry-run a écrit dans la destination." >&2
    return 1
  fi

  bash "$WORK_DIR/scripts/install.sh" --dest "$install_dir" >"$WORK_DIR/install.log"
  for folder in Catppuccin-Latte Catppuccin-Frappe Catppuccin-Macchiato Catppuccin-Mocha; do
    if [[ ! -f "$install_dir/$folder/cinnamon/cinnamon.css" ]]; then
      echo "error: $folder n'a pas été installé." >&2
      return 1
    fi
  done

  bash "$WORK_DIR/scripts/install.sh" --dest "$install_dir" --backup >"$WORK_DIR/install-backup.log"
  if [[ -z "$(find "$install_dir" -maxdepth 1 -name 'Catppuccin-Latte.bak-*' -print -quit)" ]]; then
    echo "error: --backup n'a conservé aucune sauvegarde." >&2
    return 1
  fi
  echo "  dry-run, installation et sauvegarde fonctionnent."
}

echo "Comparaison des livrables suivis :"
compare_tree previews
compare_tree dist
check_installer

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
