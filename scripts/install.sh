#!/usr/bin/env bash
# Installe les thèmes Catppuccin générés pour Cinnamon.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${HOME}/.themes"
DRY_RUN=0
BACKUP=0

usage() {
  cat <<'EOF'
Usage : scripts/install.sh [--dest DIR] [--dry-run] [--backup]

Copie chaque thème dist/Catppuccin-* dans DIR (par défaut ~/.themes, également
lu par Cinnamon). Un dossier Catppuccin-* déjà présent à la destination est
remplacé.

Options :
  --dest DIR   répertoire de destination (par défaut : ~/.themes)
  --dry-run    affiche les actions sans rien créer ni supprimer
  --backup     déplace le thème remplacé vers <nom>.bak-<horodatage> au lieu de
               le supprimer
  -h, --help   affiche cette aide

Après l'installation :
  1. Ouvrir Menu > Préférences > Thèmes (ou Paramètres système > Thèmes).
  2. Choisir Catppuccin Latte, Frappé, Macchiato ou Mocha.
  3. Appuyer sur Ctrl+Alt+Échap si le changement n'est pas immédiat.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dest)
      [[ $# -ge 2 ]] || { echo "valeur manquante pour --dest" >&2; exit 1; }
      DEST="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --backup)
      BACKUP=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "option inconnue : $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ ! -d "${ROOT}/dist" ]]; then
  echo "dist/ est absent : lancer python3 scripts/build.py" >&2
  exit 1
fi

if [[ ${DRY_RUN} -eq 0 ]]; then
  mkdir -p "${DEST}"
fi

count=0
for theme in "${ROOT}"/dist/Catppuccin-*/; do
  [[ -d "${theme}" ]] || continue
  name="$(basename "${theme}")"
  target="${DEST}/${name}"
  count=$((count + 1))

  if [[ ${DRY_RUN} -eq 1 ]]; then
    if [[ -d "${target}" ]]; then
      echo "remplacerait ${target}"
    else
      echo "installerait ${name} -> ${target}"
    fi
    continue
  fi

  if [[ -d "${target}" ]]; then
    if [[ ${BACKUP} -eq 1 ]]; then
      backup="${target}.bak-$(date +%Y%m%d-%H%M%S)"
      mv "${target}" "${backup}"
      echo "sauvegarde de ${name} -> ${backup}"
    else
      rm -rf "${target}"
      echo "remplacement de ${name} dans ${DEST}"
    fi
  fi

  cp -R "${theme}" "${target}"
  echo "installé ${name} -> ${target}"
done

if [[ ${count} -eq 0 ]]; then
  echo "aucun thème Catppuccin-* dans dist/ : lancer python3 scripts/build.py" >&2
  exit 1
fi

if [[ ${DRY_RUN} -eq 1 ]]; then
  echo
  echo "Simulation : ${count} thème(s) seraient installés dans ${DEST} ; rien n'a été écrit."
  exit 0
fi

echo
echo "Thèmes installés dans ${DEST}."
echo "Ouvrir Paramètres > Thèmes, choisir un flavor Catppuccin, puis Ctrl+Alt+Échap."
