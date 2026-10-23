#!/usr/bin/env bash
# Vérifie une installation Catppuccin dans une session Cinnamon, en lecture seule.
# À lancer sur Linux Mint : aucun fichier n'est modifié.
set -euo pipefail

DEST="${HOME}/.themes"
STATUS=0

FLAVORS=(Catppuccin-Latte Catppuccin-Frappe Catppuccin-Macchiato Catppuccin-Mocha)

usage() {
  cat <<'EOF'
Usage : scripts/verify-cinnamon.sh [--dest DIR]

Contrôle, sans rien modifier, une installation des thèmes Catppuccin :

  - session Cinnamon et version détectées ;
  - présence des quatre thèmes et de leurs fichiers obligatoires ;
  - assets référencés par chaque cinnamon.css ;
  - erreurs de thème récentes dans ~/.cinnamon/glass.log et ~/.xsession-errors.

Options :
  --dest DIR   répertoire où les thèmes sont installés (par défaut : ~/.themes)
  -h, --help   affiche cette aide

Code de sortie : 0 si tous les contrôles passent, 1 sinon. Ce script ne remplace
pas la vérification visuelle du panneau, des menus et de l'écran de verrouillage.
EOF
}

ok() { printf '  [ok]        %s\n' "$1"; }
warn() { printf '  [attention] %s\n' "$1"; }
fail() {
  printf '  [échec]     %s\n' "$1"
  STATUS=1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dest)
      [[ $# -ge 2 ]] || { echo "valeur manquante pour --dest" >&2; exit 1; }
      DEST="$2"
      shift 2
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

check_assets() {
  local name="$1" css="$2"
  local dir asset missing=0
  dir="$(dirname -- "$css")"
  while IFS= read -r asset; do
    [[ -n "$asset" ]] || continue
    if [[ ! -f "${dir}/${asset}" ]]; then
      fail "${name} : asset manquant ${asset}"
      missing=1
    fi
  done < <(grep -o 'url("[^"]*")' "$css" | sed 's/^url("//; s/")$//' | sort -u)
  return "${missing}"
}

check_theme() {
  local name="$1"
  local theme="${DEST}/${name}"
  local css="${theme}/cinnamon/cinnamon.css"
  if [[ ! -d "$theme" ]]; then
    fail "${name} absent de ${DEST}"
    return
  fi
  local missing=0 relative
  for relative in index.theme cinnamon/cinnamon.css cinnamon/thumbnail.png LICENSE; do
    if [[ ! -f "${theme}/${relative}" ]]; then
      fail "${name} : ${relative} manquant"
      missing=1
    fi
  done
  [[ ${missing} -eq 0 ]] || return
  if ! check_assets "$name" "$css"; then
    return
  fi
  ok "${name} installé (${css})"
}

scan_log() {
  local file="$1"
  local shown="${2:-5}"
  [[ -f "$file" ]] || return 0
  local matches
  matches="$(grep -inE 'cinnamon\.css|sttheme|st-theme|libcroco|failed to parse|unknown property' "$file" | tail -n "$shown" || true)"
  if [[ -n "$matches" ]]; then
    warn "entrées à vérifier dans ${file} :"
    printf '%s\n' "$matches" | sed 's/^/              /'
  else
    ok "aucune erreur de thème dans ${file}"
  fi
}

echo "Vérification Catppuccin pour Cinnamon"
echo "Thèmes recherchés dans : ${DEST}"
echo

echo "Session :"
desktop="${XDG_CURRENT_DESKTOP:-inconnu}"
session_type="${XDG_SESSION_TYPE:-inconnu}"
case "$desktop" in
  *Cinnamon*) ok "bureau ${desktop} (${session_type})" ;;
  *) warn "bureau détecté : ${desktop} (${session_type}) — ce script suppose Cinnamon" ;;
esac
if [[ "$session_type" == "wayland" ]]; then
  warn "session Wayland : le projet n'est validé que sous X11"
fi
if command -v cinnamon >/dev/null 2>&1; then
  cinnamon_version="$(cinnamon --version 2>/dev/null | head -n 1 || true)"
  ok "Cinnamon installé : ${cinnamon_version:-version non rapportée}"
else
  warn "commande cinnamon introuvable : lancer ce script dans une session Cinnamon"
fi

echo
echo "Thèmes installés :"
for flavor in "${FLAVORS[@]}"; do
  check_theme "$flavor"
done

echo
echo "Thème actif :"
if command -v gsettings >/dev/null 2>&1; then
  current="$(gsettings get org.cinnamon.theme name 2>/dev/null || true)"
  if [[ -z "$current" ]]; then
    warn "impossible de lire org.cinnamon.theme name"
  else
    case "$current" in
      *Catppuccin*) ok "thème de bureau actif : ${current}" ;;
      *) warn "thème de bureau actif : ${current} (aucun flavor Catppuccin sélectionné)" ;;
    esac
  fi
else
  warn "gsettings introuvable : impossible de lire le thème actif"
fi

echo
echo "Journaux :"
scan_log "${HOME}/.cinnamon/glass.log"
scan_log "${HOME}/.xsession-errors"

echo
if [[ ${STATUS} -eq 0 ]]; then
  echo "Tous les contrôles passent. Le rendu (panneau, menus, verrouillage) reste à vérifier à l'œil."
else
  echo "Au moins un contrôle a échoué : corriger les lignes [échec] ci-dessus." >&2
fi
exit "${STATUS}"
