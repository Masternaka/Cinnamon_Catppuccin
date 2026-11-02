#!/usr/bin/env bash
# Installe les thèmes Catppuccin pour Cinnamon, GTK et les thèmes complémentaires.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${HOME}/.themes"
COMPANIONS_DEST="${HOME}/.icons"
DRY_RUN=0
BACKUP=0
INSTALL_COMPANIONS=1

usage() {
  cat <<'EOF'
Usage : scripts/install.sh [--dest DIR] [--companions-dest DIR]
                           [--dry-run] [--backup] [--no-companions]

Copie chaque thème dist/Catppuccin-* dans DIR (par défaut ~/.themes, également
lu par Cinnamon). Un dossier Catppuccin-* déjà présent à la destination est
remplacé.

Installe aussi les thèmes complémentaires recolorés Catppuccin-Kora-Mocha
(icônes) et Catppuccin-Vimix-Mocha (curseurs) dans ~/.icons.

Options :
  --dest DIR             répertoire des thèmes Cinnamon/GTK (défaut : ~/.themes)
  --companions-dest DIR  répertoire des icônes et curseurs (défaut : ~/.icons)
  --no-companions        n'installe pas Kora ni Vimix
  --dry-run              affiche les actions sans rien créer ni supprimer
  --backup               déplace le thème remplacé vers <nom>.bak-<horodatage>
                         au lieu de le supprimer
  -h, --help             affiche cette aide

Après l'installation :
  1. Ouvrir Menu > Préférences > Thèmes (ou Paramètres système > Thèmes).
  2. Choisir Catppuccin Latte, Frappé, Macchiato ou Mocha dans la section
     Bureau, puis le même flavor dans la section Applications (GTK).
  3. Choisir Catppuccin Kora Mocha dans Icônes et Catppuccin Vimix Mocha dans
     Pointeur de la souris (facultatif).
  4. Appuyer sur Ctrl+Alt+Échap si le changement n'est pas immédiat.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dest)
      [[ $# -ge 2 ]] || { echo "valeur manquante pour --dest" >&2; exit 1; }
      DEST="$2"
      shift 2
      ;;
    --companions-dest)
      [[ $# -ge 2 ]] || { echo "valeur manquante pour --companions-dest" >&2; exit 1; }
      COMPANIONS_DEST="$2"
      shift 2
      ;;
    --no-companions)
      INSTALL_COMPANIONS=0
      shift
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

install_companion() {
  local source="$1" label="$2"
  local name target backup
  name="$(basename "${source}")"
  target="${COMPANIONS_DEST}/${name}"

  if [[ ! -d "${source}" ]]; then
    echo "thème ${label} absent : ${source}" >&2
    return 1
  fi

  if [[ ${DRY_RUN} -eq 1 ]]; then
    if [[ -d "${target}" ]]; then
      echo "remplacerait ${target}"
    else
      echo "installerait ${label} ${name} -> ${target}"
    fi
    return 0
  fi

  mkdir -p "${COMPANIONS_DEST}"
  if [[ -d "${target}" ]]; then
    if [[ ${BACKUP} -eq 1 ]]; then
      backup="${target}.bak-$(date +%Y%m%d-%H%M%S)"
      mv "${target}" "${backup}"
      echo "sauvegarde de ${name} -> ${backup}"
    else
      rm -rf "${target}"
      echo "remplacement de ${name} dans ${COMPANIONS_DEST}"
    fi
  fi

  cp -R "${source}" "${target}"
  echo "installé ${label} ${name} -> ${target}"

  if [[ "${label}" == "icônes" ]] && command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "${target}" >/dev/null 2>&1 || true
  fi
}

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

if [[ ${INSTALL_COMPANIONS} -eq 1 ]]; then
  missing=0
  if ! install_companion "${ROOT}/icons/Catppuccin-Kora-Mocha" "icônes"; then
    missing=1
  fi
  if ! install_companion "${ROOT}/cursors/Catppuccin-Vimix-Mocha" "curseurs"; then
    missing=1
  fi
  if [[ ${missing} -eq 1 ]]; then
    echo "les thèmes complémentaires source sont requis ; voir README.md" >&2
    exit 1
  fi
fi

if [[ ${DRY_RUN} -eq 1 ]]; then
  echo
  echo "Simulation : ${count} thème(s) seraient installés dans ${DEST} ; rien n'a été écrit."
  if [[ ${INSTALL_COMPANIONS} -eq 1 ]]; then
    echo "Icônes et curseurs seraient installés dans ${COMPANIONS_DEST}."
  fi
  exit 0
fi

echo
echo "Thèmes installés dans ${DEST}."
if [[ ${INSTALL_COMPANIONS} -eq 1 ]]; then
  echo "Icônes et curseurs installés dans ${COMPANIONS_DEST}."
fi
echo "Ouvrir Paramètres > Thèmes, choisir le flavor Catppuccin dans Bureau et Applications, puis Ctrl+Alt+Échap."
echo "Choisir Catppuccin Kora Mocha dans Icônes et Catppuccin Vimix Mocha dans Pointeur de la souris si souhaité."
