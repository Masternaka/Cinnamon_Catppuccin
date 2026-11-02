#!/usr/bin/env bash
# Vérifie une installation Catppuccin dans une session Cinnamon, en lecture seule.
# À lancer sur Linux Mint : aucun fichier n'est modifié.
set -euo pipefail

DEST="${HOME}/.themes"
COMPANIONS_DEST="${HOME}/.icons"
STATUS=0

FLAVORS=(Catppuccin-Latte Catppuccin-Frappe Catppuccin-Macchiato Catppuccin-Mocha)

usage() {
  cat <<'EOF'
Usage : scripts/verify-cinnamon.sh [--dest DIR] [--companions-dest DIR]

Contrôle, sans rien modifier, une installation des thèmes Catppuccin :

  - session Cinnamon et version détectées ;
  - présence des quatre thèmes et de leurs fichiers Cinnamon et GTK ;
  - assets référencés par chaque feuille de style Cinnamon et GTK ;
  - présence des thèmes complémentaires Kora (icônes) et Vimix (curseurs) ;
  - thèmes Cinnamon, GTK, icônes et curseurs actifs ;
  - erreurs de thème récentes dans ~/.cinnamon/glass.log et ~/.xsession-errors.

Options :
  --dest DIR             répertoire des thèmes (par défaut : ~/.themes)
  --companions-dest DIR  répertoire des icônes et curseurs (par défaut : ~/.icons)
  -h, --help             affiche cette aide

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
    --companions-dest)
      [[ $# -ge 2 ]] || { echo "valeur manquante pour --companions-dest" >&2; exit 1; }
      COMPANIONS_DEST="$2"
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
    case "$asset" in
      resource://*|data:*) continue ;;
    esac
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
  for relative in \
      index.theme \
      cinnamon/cinnamon.css \
      cinnamon/thumbnail.png \
      gtk-2.0/gtkrc \
      gtk-3.0/gtk.css \
      gtk-3.0/gtk-dark.css \
      gtk-3.0/thumbnail.png \
      gtk-4.0/gtk.css \
      gtk-4.0/gtk-dark.css \
      gtk-4.0/thumbnail.png \
      LICENSE; do
    if [[ ! -f "${theme}/${relative}" ]]; then
      fail "${name} : ${relative} manquant"
      missing=1
    fi
  done
  [[ ${missing} -eq 0 ]] || return
  for css in \
      "${theme}/cinnamon/cinnamon.css" \
      "${theme}/gtk-3.0/gtk.css" \
      "${theme}/gtk-3.0/gtk-dark.css" \
      "${theme}/gtk-4.0/gtk.css" \
      "${theme}/gtk-4.0/gtk-dark.css"; do
    if ! check_assets "$name" "$css"; then
      return
    fi
  done
  ok "${name} installé (Cinnamon + GTK 2/3/4)"
}

check_companions() {
  local name theme missing
  for name in Catppuccin-Kora-Mocha Catppuccin-Vimix-Mocha; do
    theme="${COMPANIONS_DEST}/${name}"
    missing=0
    if [[ ! -d "${theme}" ]]; then
      fail "${name} absent de ${COMPANIONS_DEST}"
      continue
    fi
    for relative in index.theme LICENSE NOTICE.md; do
      if [[ ! -f "${theme}/${relative}" ]]; then
        fail "${name} : ${relative} manquant"
        missing=1
      fi
    done
    if [[ "${name}" == "Catppuccin-Kora-Mocha" ]]; then
      for relative in places/scalable/folder.svg actions/symbolic/edit-copy-symbolic.svg; do
        if [[ ! -f "${theme}/${relative}" ]]; then
          fail "${name} : ${relative} manquant"
          missing=1
        fi
      done
    else
      for relative in cursors/default cursors/pointer cursors/wait; do
        if [[ ! -f "${theme}/${relative}" ]]; then
          fail "${name} : ${relative} manquant"
          missing=1
        fi
      done
    fi
    if [[ ${missing} -eq 0 ]]; then
      ok "${name} installé"
    fi
  done
}

scan_log() {
  local file="$1"
  local shown="${2:-5}"
  [[ -f "$file" ]] || return 0
  local matches
  matches="$(grep -inE 'cinnamon\.css|gtk\.css|gtkrc|sttheme|st-theme|libcroco|failed to parse|unknown property' "$file" | tail -n "$shown" || true)"
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
echo "Thèmes complémentaires :"
check_companions

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

  current_gtk="$(gsettings get org.cinnamon.desktop.interface gtk-theme 2>/dev/null || true)"
  if [[ -z "$current_gtk" ]]; then
    current_gtk="$(gsettings get org.gnome.desktop.interface gtk-theme 2>/dev/null || true)"
  fi
  if [[ -z "$current_gtk" ]]; then
    warn "impossible de lire le thème GTK actif"
  else
    case "$current_gtk" in
      *Catppuccin*) ok "thème GTK actif : ${current_gtk}" ;;
      *) warn "thème GTK actif : ${current_gtk} (aucun flavor Catppuccin sélectionné)" ;;
    esac
  fi

  current_icons="$(gsettings get org.cinnamon.desktop.interface icon-theme 2>/dev/null || true)"
  if [[ -z "$current_icons" ]]; then
    current_icons="$(gsettings get org.gnome.desktop.interface icon-theme 2>/dev/null || true)"
  fi
  if [[ -z "$current_icons" ]]; then
    warn "impossible de lire le thème d'icônes actif"
  else
    case "$current_icons" in
      *Catppuccin-Kora-Mocha*) ok "thème d'icônes actif : ${current_icons}" ;;
      *) warn "thème d'icônes actif : ${current_icons} (Catppuccin-Kora-Mocha non sélectionné)" ;;
    esac
  fi

  current_cursors="$(gsettings get org.cinnamon.desktop.interface cursor-theme 2>/dev/null || true)"
  if [[ -z "$current_cursors" ]]; then
    current_cursors="$(gsettings get org.gnome.desktop.interface cursor-theme 2>/dev/null || true)"
  fi
  if [[ -z "$current_cursors" ]]; then
    warn "impossible de lire le thème de curseurs actif"
  else
    case "$current_cursors" in
      *Catppuccin-Vimix-Mocha*) ok "thème de curseurs actif : ${current_cursors}" ;;
      *) warn "thème de curseurs actif : ${current_cursors} (Catppuccin-Vimix-Mocha non sélectionné)" ;;
    esac
  fi
else
  warn "gsettings introuvable : impossible de lire les thèmes actifs"
fi

echo
echo "Journaux :"
scan_log "${HOME}/.cinnamon/glass.log"
scan_log "${HOME}/.xsession-errors"

echo
if [[ ${STATUS} -eq 0 ]]; then
  echo "Tous les contrôles passent. Le rendu (panneau, menus, GTK, icônes, curseurs, verrouillage) reste à vérifier à l'œil."
else
  echo "Au moins un contrôle a échoué : corriger les lignes [échec] ci-dessus." >&2
fi
exit "${STATUS}"
