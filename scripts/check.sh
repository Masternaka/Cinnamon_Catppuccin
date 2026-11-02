#!/usr/bin/env bash
# Vérifications statiques dans une copie temporaire, sans modifier les livrables.
# Compare aussi dist/ et previews/ suivis à une compilation fraîche : une
# modification des gabarits sans reconstruction fait échouer le script.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf -- "$WORK_DIR"' EXIT

cd "$ROOT"
bash -n scripts/check.sh scripts/install.sh scripts/verify-cinnamon.sh
mkdir -p "$WORK_DIR/scripts"
cp scripts/build.py scripts/test_build.py scripts/install.sh scripts/verify-cinnamon.sh \
  scripts/recolor_companions.py "$WORK_DIR/scripts/"
cp palette.json LICENSE "$WORK_DIR/"
cp -R src "$WORK_DIR/src"
ln -s "$ROOT/icons" "$WORK_DIR/icons"
ln -s "$ROOT/cursors" "$WORK_DIR/cursors"
PYTHONPYCACHEPREFIX="$WORK_DIR/pycache" python3 -m py_compile \
  "$WORK_DIR/scripts/build.py" "$WORK_DIR/scripts/test_build.py" \
  "$WORK_DIR/scripts/recolor_companions.py"

echo "Tests unitaires de build.py :"
PYTHONPYCACHEPREFIX="$WORK_DIR/pycache" python3 "$WORK_DIR/scripts/test_build.py"

# --strict-contrast : un couple de couleurs sous 4,5:1 fait échouer le contrôle.
python3 "$WORK_DIR/scripts/build.py" --strict-contrast

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
  local companions_dir="$WORK_DIR/installed-companions"
  local folder
  echo "Vérification de scripts/install.sh :"

  bash "$WORK_DIR/scripts/install.sh" --dry-run \
    --dest "$install_dir" --companions-dest "$companions_dir" \
    >"$WORK_DIR/install-dry-run.log"
  if [[ -e "$install_dir" || -e "$companions_dir" ]]; then
    echo "error: --dry-run a écrit dans une destination." >&2
    return 1
  fi

  bash "$WORK_DIR/scripts/install.sh" \
    --dest "$install_dir" --companions-dest "$companions_dir" \
    >"$WORK_DIR/install.log"
  for folder in Catppuccin-Latte Catppuccin-Frappe Catppuccin-Macchiato Catppuccin-Mocha; do
    if [[ ! -f "$install_dir/$folder/cinnamon/cinnamon.css" ]]; then
      echo "error: $folder n'a pas été installé." >&2
      return 1
    fi
  done
  for folder in Catppuccin-Kora-Mocha Catppuccin-Vimix-Mocha; do
    if [[ ! -f "$companions_dir/$folder/index.theme" ]]; then
      echo "error: $folder n'a pas été installé." >&2
      return 1
    fi
  done

  bash "$WORK_DIR/scripts/install.sh" \
    --dest "$install_dir" --companions-dest "$companions_dir" --backup \
    >"$WORK_DIR/install-backup.log"
  if [[ -z "$(find "$install_dir" -maxdepth 1 -name 'Catppuccin-Latte.bak-*' -print -quit)" ]]; then
    echo "error: --backup n'a conservé aucune sauvegarde de thème." >&2
    return 1
  fi
  if [[ -z "$(find "$companions_dir" -maxdepth 1 -name 'Catppuccin-Kora-Mocha.bak-*' -print -quit)" ]]; then
    echo "error: --backup n'a conservé aucune sauvegarde d'icônes." >&2
    return 1
  fi

  # HOME factice : le contrôle ne lit pas les journaux de la machine.
  mkdir -p "$WORK_DIR/fakehome"
  if ! HOME="$WORK_DIR/fakehome" bash "$WORK_DIR/scripts/verify-cinnamon.sh" \
      --dest "$install_dir" --companions-dest "$companions_dir" \
      >"$WORK_DIR/verify.log" 2>&1; then
    echo "error: verify-cinnamon.sh a signalé un échec sur l'installation temporaire." >&2
    sed 's/^/  /' "$WORK_DIR/verify.log" >&2
    return 1
  fi
  echo "  dry-run, installation, sauvegarde et vérification fonctionnent."
}

check_companions() {
  echo "Vérification des thèmes complémentaires :"
  local path
  for path in \
      icons/Catppuccin-Kora-Mocha/index.theme \
      icons/Catppuccin-Kora-Mocha/LICENSE \
      icons/Catppuccin-Kora-Mocha/NOTICE.md \
      cursors/Catppuccin-Vimix-Mocha/index.theme \
      cursors/Catppuccin-Vimix-Mocha/LICENSE \
      cursors/Catppuccin-Vimix-Mocha/NOTICE.md; do
    if [[ ! -f "$ROOT/$path" ]]; then
      echo "error: $path manquant." >&2
      return 1
    fi
  done
  if find "$ROOT/icons/Catppuccin-Kora-Mocha" -name icon-theme.cache -print -quit | grep -q .; then
    echo "error: icon-theme.cache obsolète présent dans le thème Kora." >&2
    return 1
  fi
  if ! (cd "$WORK_DIR" && python3 scripts/recolor_companions.py --check) \
      >"$WORK_DIR/companions-check.log" 2>&1; then
    echo "error: les thèmes Kora/Vimix ne sont pas à jour ; lancer python3 scripts/recolor_companions.py." >&2
    sed 's/^/  /' "$WORK_DIR/companions-check.log" >&2
    return 1
  fi
  echo "  icônes et curseurs recolorés, licences et notices présentes."
}

echo "Comparaison des livrables suivis :"
compare_tree previews
compare_tree dist
check_companions
check_installer

python3 - "$WORK_DIR" <<'PY'
from pathlib import Path
import re
import struct
import sys
from zipfile import ZipFile

root = Path(sys.argv[1])
folders = [f"Catppuccin-{name}" for name in ("Latte", "Frappe", "Macchiato", "Mocha")]
required = (
    "LICENSE",
    "index.theme",
    "cinnamon/cinnamon.css",
    "cinnamon/thumbnail.png",
    "gtk-2.0/gtkrc",
    "gtk-3.0/gtk.css",
    "gtk-3.0/gtk-dark.css",
    "gtk-3.0/thumbnail.png",
    "gtk-4.0/gtk.css",
    "gtk-4.0/gtk-dark.css",
    "gtk-4.0/thumbnail.png",
)
thumbs = (
    ("cinnamon/thumbnail.png", (247, 60)),
    ("gtk-3.0/thumbnail.png", (120, 36)),
    ("gtk-4.0/thumbnail.png", (120, 36)),
)
css_files = (
    "cinnamon/cinnamon.css",
    "gtk-3.0/gtk.css",
    "gtk-3.0/gtk-dark.css",
    "gtk-4.0/gtk.css",
    "gtk-4.0/gtk-dark.css",
)
for folder in folders:
    theme = root / "dist" / folder
    for relative in required:
        if not (theme / relative).is_file():
            raise ValueError(f"Fichier manquant : {folder}/{relative}")

    for relative, expected in thumbs:
        data = (theme / relative).read_bytes()[:24]
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError(f"PNG invalide : {folder}/{relative}")
        width, height = struct.unpack(">II", data[16:24])
        if (width, height) != expected:
            raise ValueError(
                f"Dimensions inattendues : {folder}/{relative} = {width}x{height}, "
                f"attendu {expected[0]}x{expected[1]}"
            )

    for relative in css_files:
        css_path = theme / relative
        for value in re.findall(r"url\(\s*([^)]*?)\s*\)", css_path.read_text()):
            asset = value.strip("\"'")
            if asset.startswith(("resource://", "data:")):
                continue
            if not (css_path.parent / asset).is_file():
                raise ValueError(f"Asset CSS manquant : {folder}/{relative} -> {asset}")

    gtk2 = (theme / "gtk-2.0/gtkrc").read_text()
    leftover = re.search(r"@[A-Za-z0-9_-]+@", gtk2)
    if leftover:
        raise ValueError(f"Jeton non résolu : {folder}/gtk-2.0/gtkrc {leftover.group(0)}")

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


def tree_entries(source):
    for entry in sorted(source.iterdir(), key=lambda path: path.name):
        if entry.name == ".DS_Store":
            continue
        if entry.is_symlink():
            yield entry
        elif entry.is_dir():
            yield from tree_entries(entry)
        else:
            yield entry


for archive_name, source_dir, prefix in (
    (
        "Catppuccin-Kora-Mocha-Icons.zip",
        root / "icons" / "Catppuccin-Kora-Mocha",
        "Catppuccin-Kora-Mocha",
    ),
    (
        "Catppuccin-Vimix-Mocha-Cursors.zip",
        root / "cursors" / "Catppuccin-Vimix-Mocha",
        "Catppuccin-Vimix-Mocha",
    ),
):
    archive_path = root / "dist" / archive_name
    with ZipFile(archive_path) as archive:
        if archive.testzip() is not None:
            raise ValueError(f"Archive corrompue : {archive_name}")
        entries = list(tree_entries(source_dir))
        expected = {
            (Path(prefix) / entry.relative_to(source_dir)).as_posix()
            for entry in entries
        }
        if set(archive.namelist()) != expected:
            raise ValueError(f"Contenu incorrect : {archive_name}")
        for entry in entries:
            if entry.is_symlink():
                name = (Path(prefix) / entry.relative_to(source_dir)).as_posix()
                mode = archive.getinfo(name).external_attr >> 16
                if mode != 0o120777:
                    raise ValueError(f"Lien symbolique incorrect : {archive_name}/{name}")

print(
    "Vérifications réussies : quatre thèmes Cinnamon + GTK, "
    "thèmes Kora/Vimix et sept archives."
)
PY
