# Guide pour les assistants IA

Ces instructions s’appliquent à tout le dépôt `Cinnamon_Catppuccin`. Respecter la
demande de l’utilisateur et les instructions plus précises d’un éventuel
sous-dossier.

## Comprendre le projet

**Cinnamon_Catppuccin** est un thème pour l’interface Cinnamon de Linux Mint et
pour les applications GTK, décliné dans les quatre flavors officiels de
[Catppuccin](https://catppuccin.com/palette/) : **Latte**, **Frappé**,
**Macchiato** et **Mocha**.

Le dépôt ne contient **pas** d’extension Cinnamon, de code GJS, de
`metadata.json` ni de `settings-schema.json`. Il ne faut pas les introduire par
analogie avec une extension : le livrable est un ensemble de thèmes
installables (Cinnamon + GTK) et de thèmes complémentaires (icônes + curseurs).

Le thème couvre le shell Cinnamon : panneau (quatre orientations), menus
classique et nouveau menu 6.6+, applets, listes de fenêtres, Alt-Tab,
notifications, OSD, calendrier, dialogues, écran de verrouillage, Expo,
desklets, IBus et clavier virtuel. Il fournit aussi un thème GTK 2, GTK 3 et
GTK 4 généré depuis la même palette ; la partie GTK importe Adwaita et le
recolore. Des thèmes complémentaires recolorés fournissent les icônes (Kora) et
les curseurs (Vimix) en Mocha avec l’accent mauve ; les icônes d’applications
gardent leurs couleurs de marque. Les décorations de fenêtres (Metacity/Muffin)
restent hors périmètre.

La cible documentée est Cinnamon 5.x/6.x sous X11. Le menu classique et le
nouveau menu sont tous les deux stylés, mais le rendu réel n’est validé que
dans une session Cinnamon/X11. Le rendu GTK 3/GTK 4, des icônes et des
curseurs n’est pas validé sur macOS et les applications libadwaita ignorent en
grande partie les thèmes GTK tiers. Wayland n’est pas validé. Une compilation
réussie ne prouve pas un essai graphique réel.

## Documentation de référence : Markdown dans le dépôt

Toute la documentation doit rester **exclusivement en Markdown dans le dépôt**,
sans rédaction ni mise à jour dans Notion.

- `README.md` est le point d’entrée : présentation, variantes, installation,
  compilation, structure et limites.
- `AGENTS.md` contient les consignes opérationnelles.
- `.github/copilot-instructions.md` renvoie aux consignes communes ; il ne doit
  pas citer de dossier `docs/` tant que celui-ci n’existe pas.
- Si des guides, plans ou comptes rendus sont ajoutés, les placer dans `docs/`
  et les référencer depuis `README.md`. Ne pas créer de doubles locaux
  concurrents.

Lorsqu’une tâche change le fonctionnement, les commandes, la structure, la
compatibilité ou les limites, actualiser `README.md` et `AGENTS.md` dans la même
tâche. Vérifier les liens, les chemins et les commandes. Ne pas annoncer une
suite de tests ou une validation Cinnamon qui n’existe pas.

## Structure et fichiers à modifier

| Chemin | Responsabilité |
| --- | --- |
| `palette.json` | Palette officielle des quatre flavors ; source de vérité des couleurs. |
| `src/cinnamon.css.in` | Gabarit CSS Cinnamon avec jetons `@nom@`. |
| `src/gtk3.css.in` | Gabarit CSS GTK 3 (importe Adwaita puis recolore les widgets). |
| `src/gtk4.css.in` | Gabarit CSS GTK 4 (importe Adwaita puis recolore les widgets). |
| `src/gtk2.gtkrc.in` | Gabarit GTK 2 limité aux couleurs et aux marges de base. |
| `src/index.theme.in` | Métadonnées générées dans chaque thème. |
| `src/overview.html.in` | Gabarit de la galerie HTML autonome. |
| `scripts/build.py` | Génération des CSS Cinnamon et GTK, des assets, des vignettes PNG, des aperçus et des archives. |
| `scripts/recolor_companions.py` | Recoloration idempotente de Kora et Vimix (Mocha, accent mauve). |
| `scripts/install.sh` | Copie des thèmes vers `~/.themes`/`--dest` et des complémentaires vers `~/.icons`/`--companions-dest`. |
| `icons/Catppuccin-Kora-Mocha/` | Thème d’icônes dérivé de Kora (GPL-3.0), recoloré pour Mocha. |
| `cursors/Catppuccin-Vimix-Mocha/` | Thème de curseurs dérivé de Vimix (GPL-3.0), recoloré pour Mocha. |
| `Makefile` | Raccourcis `build`, `check`, `install`, `clean`, `preview`, `companions`. |
| `dist/` | Thèmes prêts à installer et sept archives zip ; **artefacts générés mais suivis**. |
| `previews/` | Aperçus SVG et galerie HTML ; **artefacts générés mais suivis**. |
| `README.md` | Documentation utilisateur en français. |
| `AGENTS.md` | Consignes opérationnelles. |
| `LICENSE` | Licence MIT du code Cinnamon/GTK ; les dossiers `icons/` et `cursors/` restent sous GPL-3.0. |
| `scripts/check.sh` | Contrôles statiques, tests unitaires, compilation temporaire, comparaison de `dist/`/`previews/`, contrôle de la recoloration et test de l’installateur ; utilisé par la CI. |
| `scripts/test_build.py` | Tests unitaires des helpers de `build.py` (contrastes, couleurs, jetons, validation CSS). |
| `scripts/verify-cinnamon.sh` | Vérification en lecture seule d’une installation Cinnamon + GTK + icônes/curseurs dans une session Cinnamon. |
| `.github/workflows/` | `ci.yml` (contrôles + compilation avec un second accent) et `release.yml` (release en brouillon, voir ci-dessous). |
| `.github/dependabot.yml` | Mises à jour mensuelles des actions GitHub. |
| `.gitattributes` | Fins de ligne LF, archives ZIP, PNG et fichiers Xcursor traités comme binaires. |

Chaque thème généré a cette forme :

```text
Catppuccin-Mocha/
├── LICENSE
├── index.theme
├── cinnamon/
│   ├── cinnamon.css
│   ├── thumbnail.png
│   ├── checkbox-off.svg
│   ├── checkbox.svg
│   ├── radio-off.svg
│   ├── radio.svg
│   ├── toggle-off.svg
│   ├── toggle-on.svg
│   ├── calendar-arrow-*.svg
│   ├── add-workspace*.svg
│   ├── close.svg
│   ├── trash-icon.svg
│   └── corner-ripple.png
├── gtk-2.0/
│   └── gtkrc
├── gtk-3.0/
│   ├── gtk.css
│   ├── gtk-dark.css
│   ├── thumbnail.png
│   └── assets/
│       ├── check.svg
│       ├── check-mixed.svg
│       ├── radio.svg
│       ├── check-disabled.svg
│       ├── check-mixed-disabled.svg
│       └── radio-disabled.svg
└── gtk-4.0/
    ├── gtk.css
    ├── gtk-dark.css
    ├── thumbnail.png
    └── assets/ (mêmes fichiers que gtk-3.0/assets)
```

Les thèmes complémentaires sont des dossiers séparés, installés dans
`~/.icons` :

```text
icons/Catppuccin-Kora-Mocha/
├── LICENSE                       # GPL-3.0 (Kora)
├── NOTICE.md
├── index.theme
├── actions/ … status/            # SVG recoloriés ; apps/ préservé
└── create-new-icon-theme.cache.sh

cursors/Catppuccin-Vimix-Mocha/
├── LICENSE                       # GPL-3.0 (Vimix-cursors)
├── NOTICE.md
├── index.theme
└── cursors/
```

Le nom du dossier reste ASCII (`Catppuccin-Frappe`) ; le nom affiché peut être
accentué (`Frappé`). Cinnamon détecte le thème de bureau par la présence de
`cinnamon/cinnamon.css` et utilise `cinnamon/thumbnail.png` dans le sélecteur.
La section Applications détecte le thème GTK par `gtk-3.0/gtk.css` (et
`gtk-2.0/gtkrc` pour les applications GTK 2) ; `gtk-3.0/thumbnail.png` fournit
l’aperçu. `index.theme` fournit les métadonnées et déclare `GtkTheme` avec le
nom du dossier. Ne pas ajouter de `theme.json` sans vérification de la version
de Cinnamon.

Ne pas éditer à la main les fichiers de `dist/` ni les aperçus de `previews/` :
modifier les gabarits, `palette.json` ou `scripts/build.py`, puis reconstruire.
`make clean` supprime `dist/` et `previews/` ; `make build` les régénère.
Ne pas éditer à la main les SVG de Kora ni les fichiers Xcursor de Vimix :
modifier les sources puis relancer `python3 scripts/recolor_companions.py`
(`make companions`). Le script est idempotent et préserve les logos `apps/`.

## Construire et vérifier

Le projet ne requiert que Python 3 et sa bibliothèque standard, ainsi que Bash
pour l’installation. Il n’y a ni Sass, ni Pillow, ni dépendance Node.js.

Depuis la racine :

```sh
make build
# ou
python3 scripts/build.py
```

Changer la couleur d’accentuation sans modifier les flavors :

```sh
make ACCENT=blue
# ou
python3 scripts/build.py --accent blue
```

Reconstruire depuis zéro :

```sh
make clean && make build
```

Régénérer les icônes Kora et les curseurs Vimix recolorés :

```sh
python3 scripts/recolor_companions.py
# ou
make companions
```

Le script est idempotent et ne touche qu’aux catégories d’interface de Kora ;
les icônes `apps/` gardent leurs couleurs de marque.

Le build doit produire :

- quatre dossiers `dist/Catppuccin-{Latte,Frappe,Macchiato,Mocha}/`, chacun avec
  Cinnamon et GTK 2/3/4 ;
- quatre archives individuelles et `dist/Catppuccin-Cinnamon-all-flavors.zip` ;
- `dist/Catppuccin-Kora-Mocha-Icons.zip` et
  `dist/Catppuccin-Vimix-Mocha-Cursors.zip`, avec leurs liens symboliques ;
- `previews/Catppuccin-*.svg` et `previews/overview.html`.

Le script vérifie les accolades et les jetons CSS Cinnamon et GTK, l’absence de
jetons non résolus, la validité XML des SVG, la taille 247 × 60 des vignettes
Cinnamon et 120 × 36 des vignettes GTK, et la présence des fichiers générés. Les
aperçus obsolètes de `previews/` sont supprimés au passage. Vérifier aussi les
références `url(...)` des CSS, l’intégrité des sept archives, les liens
symboliques des thèmes complémentaires et les liens du README après toute
modification.

Contrôle commun à la CI et au développement local :

```sh
make check
# ou
bash scripts/check.sh
```

Ce script compile dans une copie temporaire sans modifier `dist/` ni
`previews/`, exécute `scripts/test_build.py`, vérifie les syntaxes Bash/Python,
les assets référencés par les CSS Cinnamon et GTK, les fichiers GTK obligatoires,
la recoloration idempotente de Kora/Vimix, la présence de leurs licences GPL-3.0
et notices, et le contenu et l’intégrité des sept archives (liens symboliques
compris). Il compare aussi les artefacts suivis (`dist/` et `previews/`) à cette
compilation fraîche : un gabarit modifié sans reconstruction le fait échouer,
avec la consigne de relancer `python3 scripts/build.py`. Il teste enfin
`scripts/install.sh` dans un répertoire temporaire (`--dry-run`, installation
des quatre thèmes et des deux complémentaires, `--backup`). Il ne valide pas
Cinnamon ni le rendu GTK/icônes/curseurs.

`scripts/check.sh` compile avec `--strict-contrast` : un couple de couleurs
sous 4,5:1 fait échouer le contrôle. Pour un diagnostic local,
`python3 scripts/build.py` affiche la liste des couples concernés sans échouer.

Les archives zip sont générées avec une date d’entrée fixe : deux compilations
identiques produisent des fichiers identiques octet pour octet, ce qui évite de
salir `dist/*.zip` à chaque build. `SOURCE_DATE_EPOCH` est respectée si elle est
définie ; l’archive dépend ensuite de la version de Python et de zlib utilisée
(la CI est en Python 3.12).

Contrôles statiques complémentaires :

```sh
bash -n scripts/install.sh scripts/verify-cinnamon.sh
python3 -m py_compile scripts/build.py scripts/recolor_companions.py
python3 scripts/recolor_companions.py --check
git diff --check
```

`git diff --check` ne couvre que les fichiers suivis ; examiner aussi les
fichiers non suivis. Les contrôles sur macOS ne valident ni StTheme/libcroco,
ni le rendu Cinnamon, ni le multi-écran.

### Recette réelle

Pour une livraison, tester sur Cinnamon/X11 :

1. Installer dans un répertoire temporaire avec
   `./scripts/install.sh --dest "$(mktemp -d)" --companions-dest "$(mktemp -d)"`,
   puis copier les thèmes dans un environnement Cinnamon de test. Une fois
   installés, lancer `./scripts/verify-cinnamon.sh --dest <répertoire>
   --companions-dest <répertoire-icônes>` : le script vérifie la session, la
   présence des fichiers et des assets Cinnamon et GTK, celle de Kora/Vimix, les
   thèmes actifs et les erreurs de thème dans `~/.cinnamon/glass.log` et
   `~/.xsession-errors`.
2. Choisir chaque flavor dans **Paramètres → Thèmes**, dans **Bureau** puis dans
   **Applications**, et redémarrer Cinnamon si nécessaire avec
   **Ctrl+Alt+Échap**.
3. Choisir **Catppuccin Kora Mocha** dans **Icônes** et
   **Catppuccin Vimix Mocha** dans **Pointeur de la souris**.
4. Vérifier le panneau sur les quatre orientations, les menus classique et 6.6+
   si disponibles, les applets, les listes de fenêtres, les notifications, les
   dialogues, le calendrier, l’écran de verrouillage, Expo et le clavier.
5. Ouvrir des applications GTK 3 (Nemo, Xed, Terminal, Paramètres) et une
   application GTK 4 si disponible : boutons, entrées, menus, listes,
   sélections, cases à cocher et infobulles doivent suivre la palette. Vérifier
   aussi les dossiers dans Nemo et les curseurs (défaut, texte, redimensionnement,
   attente, copie et interdiction).
6. Consulter `~/.cinnamon/glass.log` et `~/.xsession-errors` en cas d’erreur.
7. Consigner la version de Cinnamon, la distribution et les résultats. Si
   l’environnement Cinnamon est indisponible, indiquer explicitement la
   validation restante.

Ne pas exécuter l’installateur réel dans `~/.themes` sans accord explicite de
l’utilisateur : le script remplace les dossiers `Catppuccin-*` déjà présents.
Préserver les personnalisations et utiliser un répertoire temporaire pour les
essais.

### Prudence sur macOS

Sur macOS, éviter de lancer Chrome headless, `qlmanage` ou d’autres outils
graphiques sur les fichiers de l’utilisateur pour vérifier les aperçus. Le build
génère déjà les vignettes et les aperçus en Python ; la galerie HTML peut être
rendue par l’application. Ces outils peuvent déclencher des alertes de
confidentialité macOS (accès au Bureau, au centre de notifications ou à TCC) et
ne sont pas nécessaires au fonctionnement du thème.

## Règles de couleurs et de CSS

- `palette.json` reprend les valeurs officielles Catppuccin. Ne pas modifier
  une valeur isolée pour un ajustement visuel sans mettre à jour la source,
  signaler l’écart et régénérer les quatre flavors.
- Les gabarits CSS utilisent des jetons `@palette@`, `@accent@`, `@panel@`,
  etc. Le build les remplace et génère aussi les variantes alpha (`@text_a80@`).
  Aucun jeton ne doit subsister dans le CSS final, y compris dans les gabarits
  GTK et le fichier GTK 2.
- Le CSS Cinnamon est interprété par StTheme/libcroco, pas par GTK, Chromium ou
  Sass. Éviter les variables CSS, les fonctions Sass et les propriétés modernes
  non prises en charge ; les propriétés inconnues peuvent être ignorées.
- Le CSS GTK est interprété par GTK 3 et GTK 4, séparément. Les gabarits
  importent Adwaita par `resource://` puis surchargent les couleurs et les
  widgets courants ; conserver cette base pour couvrir les widgets non stylés.
  Les applications libadwaita ignorent en grande partie les thèmes GTK tiers :
  ne pas promettre qu’elles suivront la palette.
- Conserver les sélecteurs du menu classique et ceux du nouveau menu Cinnamon
  6.6+ ; ne pas en supprimer un parce que la version locale ne l’utilise pas.
- Toute couleur dépendant du flavor doit passer par un jeton. Ne pas copier une
  couleur de Mocha dans un autre thème ni coder une couleur en dur dans un
  asset propre à une flavor.
- Le mauve est l’accent par défaut du dépôt ; `ACCENT=blue` restaure le bleu.
  `Base` sert de texte sur accent. Le panneau utilise `Crust`, les menus
  `Base`, les barres latérales et sous-menus `Mantle`.
- Le texte coloré doit passer par les jetons de contraste dérivés
  (`@text_secondary@`, `@text_success@`, `@text_warning@`, `@text_error@`,
  `@text_info@`, `@link@`, `@link_hover@`) et non par `@subtext0@`, `@green@`,
  `@yellow@`, `@red@` ou `@blue@` : ces derniers restent réservés aux
  remplissages, bordures et indicateurs. Le build ajuste uniquement la
  luminosité pour atteindre 4,5:1 ; ne pas « corriger » un écart en modifiant
  `palette.json`.
- `@on_accent@` vaut `Base` tant que le couple atteint 4,5:1 (cas des flavors
  sombres). Sinon le build retient la meilleure des deux couleurs `Base`/`Text`
  et n’en ajuste que la luminosité : un accent clair (jaune, pêche) reçoit donc
  un texte foncé, jamais un texte clair illisible. `@on_success@`,
  `@on_warning@`, `@on_error@` et `@on_info@` suivent la même règle pour les
  remplissages sémantiques GTK.
- Les assets SVG/PNG sont générés pour chaque flavor, y compris les glyphes
  check/radio GTK et les vignettes. Le texte des vignettes est volontairement
  simple ; ne pas dépendre d’une police externe.
- Les thèmes Kora et Vimix sont recolorés une seule fois pour **Mocha avec
  l’accent mauve** par `scripts/recolor_companions.py`. La recoloration reste
  proche de Kora : seuls les cinq couleurs du schéma, les bleus des dossiers
  et les accents des curseurs sont ajustés ; les autres couleurs, blancs et
  gris sont conservés pour la lisibilité. Ne pas éditer leurs SVG ou fichiers
  Xcursor à la main : modifier les sources puis relancer le script. Les icônes
  `apps/` de Kora sont volontairement préservées. Ces deux dossiers
  sont sous GPL-3.0 : conserver `LICENSE`, `NOTICE.md` et l’attribution.
- Conserver les quatre flavors, les accents configurables et les aperçus. La
  documentation et les commentaires destinés à l’utilisateur restent en
  français.

## Données et configuration à préserver

- Ne pas supprimer ni remplacer la configuration personnelle de l’utilisateur :
  `~/.themes`, `~/.local/share/themes`, `~/.icons`, `~/.local/share/icons`, les
  préférences Cinnamon et les fichiers de `~/.config` ne doivent être modifiés
  qu’avec un accord explicite.
- L’installateur copie les thèmes générés et remplace les dossiers
  `Catppuccin-*` présents dans la destination ; prévenir l’utilisateur avant
  toute installation réelle. Utiliser `--dest` et `--companions-dest` vers des
  répertoires temporaires, `--dry-run` pour simuler, `--backup` pour conserver
  l’ancienne version ou `--no-companions` pour ne pas installer Kora/Vimix.
- `dist/` et `previews/` sont des artefacts générés, mais ils font partie du
  livrable et sont suivis par Git. Ne pas y ajouter de captures temporaires, de
  caches, de secrets ou de données personnelles. Les fichiers ignorés
  (`__pycache__`, `.DS_Store`) ne doivent pas être versionnés.
- La licence du code Cinnamon/GTK est MIT ; la palette et le guide de style
  Catppuccin sont crédités dans le README et sous licence MIT. Les dossiers
  `icons/Catppuccin-Kora-Mocha/` et `cursors/Catppuccin-Vimix-Mocha/` restent
  sous GPL-3.0 : conserver leurs `LICENSE`, `NOTICE.md` et attributions.

## CI, releases, commits et publication

**Ne jamais créer de commit, effectuer de push, créer un tag, une pull request
ou une Release sans confirmation explicite de l’utilisateur.** Une demande de
modification ou de documentation ne vaut pas autorisation. Une autorisation de
commit seule n’autorise pas le push.

Pour ces opérations, utiliser le skill **github-commit-push** s’il est
disponible ; signaler son absence. Écrire les messages de commit en français,
avec un titre court et une description concise expliquant la raison du
changement. Demander confirmation avant toute autre écriture GitHub.

Le workflow `ci.yml` exécute `bash scripts/check.sh` avec Python 3.12 sous
Ubuntu 24.04 pour les push sur `main` et les pull requests, puis compile une
seconde fois avec `--accent blue --strict-contrast` pour détecter un jeton
propre à l’accent par défaut et tout écart de contraste.

Le workflow `release.yml` est adapté au thème :
- il se déclenche sur un tag `v*` ou manuellement avec un tag en paramètre ;
- il exécute `scripts/check.sh`, donc `dist/` et `previews/` suivis doivent être
  à jour ;
- il exige que le tag existe et pointe sur le commit courant, sans jamais
  déplacer un tag ;
- il vérifie les sept archives puis crée une release **en brouillon** intitulée
  « Catppuccin pour Cinnamon et GTK <tag> » avec
  `Catppuccin-{Latte,Frappe,Macchiato,Mocha}.zip`,
  `Catppuccin-Cinnamon-all-flavors.zip`,
  `Catppuccin-Kora-Mocha-Icons.zip` et
  `Catppuccin-Vimix-Mocha-Cursors.zip`.

Il n’y a ni `metadata.json` ni numéro de version dans le dépôt : le tag fait
foi. Ne jamais déplacer un tag existant ni remplacer une Release existante, et
ne pas publier le brouillon sans confirmation explicite de l’utilisateur. Un
push autorisé sur `main` déclenche la CI ; un tag `v*` déclenche la préparation
d’une release. Distinguer paquet local, CI distante, brouillon créé et version
réellement publiée.

## Compte rendu

Répondre en français. Indiquer le résultat, les fichiers importants, les
vérifications effectuées et leurs limites, ainsi que les validations restantes.
Mentionner explicitement l’absence de test dans une session Cinnamon réelle
lorsque c’est le cas. Ne pas masquer un contrôle ignoré ou une CI non exécutée.
