# Guide pour les assistants IA

Ces instructions s’appliquent à tout le dépôt `Cinnamon_Catppuccin`. Respecter la
demande de l’utilisateur et les instructions plus précises d’un éventuel
sous-dossier.

## Comprendre le projet

**Cinnamon_Catppuccin** est un thème pour l’interface Cinnamon de Linux Mint,
décliné dans les quatre flavors officiels de
[Catppuccin](https://catppuccin.com/palette/) : **Latte**, **Frappé**,
**Macchiato** et **Mocha**.

Le dépôt ne contient **pas** d’extension Cinnamon, de code GJS, de
`metadata.json` ni de `settings-schema.json`. Il ne faut pas les introduire par
analogie avec une extension : le livrable est un ensemble de thèmes Cinnamon
installables.

Le thème couvre le shell Cinnamon : panneau (quatre orientations), menus
classique et nouveau menu 6.6+, applets, listes de fenêtres, Alt-Tab,
notifications, OSD, calendrier, dialogues, écran de verrouillage, Expo,
desklets, IBus et clavier virtuel. Il ne couvre pas les applications GTK, les
icônes, les curseurs ni les décorations de fenêtres ; ces éléments relèvent
d’autres thèmes.

La cible documentée est Cinnamon 5.x/6.x sous X11. Le menu classique et le
nouveau menu sont tous les deux stylés, mais le rendu réel n’est validé que
dans une session Cinnamon/X11. Wayland n’est pas validé. Une compilation
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
| `src/index.theme.in` | Métadonnées générées dans chaque thème. |
| `src/overview.html.in` | Gabarit de la galerie HTML autonome. |
| `scripts/build.py` | Génération du CSS, des assets, des vignettes PNG, des aperçus et des archives. |
| `scripts/install.sh` | Copie des thèmes générés vers `~/.themes` ou un répertoire `--dest`. |
| `Makefile` | Raccourcis `build`, `check`, `install`, `clean`, `preview`. |
| `dist/` | Thèmes prêts à installer et archives zip ; **artefacts générés mais suivis**. |
| `previews/` | Aperçus SVG et galerie HTML ; **artefacts générés mais suivis**. |
| `README.md` | Documentation utilisateur en français. |
| `AGENTS.md` | Consignes opérationnelles. |
| `LICENSE` | Licence MIT du code du thème. |
| `scripts/check.sh` | Contrôles statiques, tests unitaires, compilation temporaire, comparaison de `dist/`/`previews/` et test de l’installateur ; utilisé par la CI. |
| `scripts/test_build.py` | Tests unitaires des helpers de `build.py` (contrastes, couleurs, jetons, validation CSS). |
| `scripts/verify-cinnamon.sh` | Vérification en lecture seule d’une installation dans une session Cinnamon. |
| `.github/workflows/` | `ci.yml` (contrôles + compilation avec un second accent) et `release.yml` (release en brouillon, voir ci-dessous). |
| `.github/dependabot.yml` | Mises à jour mensuelles des actions GitHub. |
| `.gitattributes` | Fins de ligne LF, archives ZIP et PNG traités comme binaires. |

Chaque thème généré a cette forme :

```text
Catppuccin-Mocha/
├── LICENSE
├── index.theme
└── cinnamon/
    ├── cinnamon.css
    ├── thumbnail.png
    ├── checkbox-off.svg
    ├── checkbox.svg
    ├── radio-off.svg
    ├── radio.svg
    ├── toggle-off.svg
    ├── toggle-on.svg
    ├── calendar-arrow-*.svg
    ├── add-workspace*.svg
    ├── close.svg
    ├── trash-icon.svg
    └── corner-ripple.png
```

Le nom du dossier reste ASCII (`Catppuccin-Frappe`) ; le nom affiché peut être
accentué (`Frappé`). Cinnamon détecte un thème par la présence de
`cinnamon/cinnamon.css` et utilise `cinnamon/thumbnail.png` dans le sélecteur.
`index.theme` fournit les métadonnées. Ne pas ajouter de `theme.json` sans
vérification de la version de Cinnamon.

Ne pas éditer à la main les fichiers de `dist/` ni les aperçus de `previews/` :
modifier les gabarits, `palette.json` ou `scripts/build.py`, puis reconstruire.
`make clean` supprime `dist/` et `previews/` ; `make build` les régénère.

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
make ACCENT=mauve
# ou
python3 scripts/build.py --accent mauve
```

Reconstruire depuis zéro :

```sh
make clean && make build
```

Le build doit produire :

- quatre dossiers `dist/Catppuccin-{Latte,Frappe,Macchiato,Mocha}/` ;
- quatre archives individuelles et `dist/Catppuccin-Cinnamon-all-flavors.zip` ;
- `previews/Catppuccin-*.svg` et `previews/overview.html`.

Le script vérifie les accolades et les jetons CSS, l’absence de jetons non
résolus, la validité XML des SVG, la taille 247 × 60 des vignettes et la
présence des fichiers générés. Les aperçus obsolètes de `previews/` sont
supprimés au passage. Vérifier aussi les références `url(...)` du CSS,
l’intégrité des archives et les liens du README après toute modification.

Contrôle commun à la CI et au développement local :

```sh
make check
# ou
bash scripts/check.sh
```

Ce script compile dans une copie temporaire sans modifier `dist/` ni
`previews/`, exécute `scripts/test_build.py`, vérifie les syntaxes Bash/Python,
les assets référencés par le CSS
et le contenu et l’intégrité des cinq archives. Il compare aussi les artefacts
suivis (`dist/` et `previews/`) à cette compilation fraîche : un gabarit modifié
sans reconstruction le fait échouer, avec la consigne de relancer
`python3 scripts/build.py`. Il teste enfin `scripts/install.sh` dans un
répertoire temporaire (`--dry-run`, installation des quatre thèmes, `--backup`).
Il ne valide pas Cinnamon.

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
bash -n scripts/install.sh
python3 -m py_compile scripts/build.py
git diff --check
```

`git diff --check` ne couvre que les fichiers suivis ; examiner aussi les
fichiers non suivis. Les contrôles sur macOS ne valident ni StTheme/libcroco,
ni le rendu Cinnamon, ni le multi-écran.

### Recette réelle

Pour une livraison, tester sur Cinnamon/X11 :

1. Installer dans un répertoire temporaire avec
   `./scripts/install.sh --dest "$(mktemp -d)"`, puis copier les thèmes dans un
   environnement Cinnamon de test. Une fois installés, lancer
   `./scripts/verify-cinnamon.sh --dest <répertoire>` : le script vérifie la
   session, la présence des fichiers et des assets, et les erreurs de thème dans
   `~/.cinnamon/glass.log` et `~/.xsession-errors`.
2. Choisir chaque flavor dans **Paramètres → Thèmes** et redémarrer Cinnamon si
   nécessaire avec **Ctrl+Alt+Échap**.
3. Vérifier le panneau sur les quatre orientations, les menus classique et 6.6+
   si disponibles, les applets, les listes de fenêtres, les notifications, les
   dialogues, le calendrier, l’écran de verrouillage, Expo et le clavier.
4. Consulter `~/.cinnamon/glass.log` et `~/.xsession-errors` en cas d’erreur.
5. Consigner la version de Cinnamon, la distribution et les résultats. Si
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
- Le gabarit CSS utilise des jetons `@palette@`, `@accent@`, `@panel@`, etc.
  Le build les remplace et génère aussi les variantes alpha (`@text_a80@`).
  Aucun jeton ne doit subsister dans le CSS final.
- Le CSS Cinnamon est interprété par StTheme/libcroco, pas par GTK, Chromium ou
  Sass. Éviter les variables CSS, les fonctions Sass et les propriétés modernes
  non prises en charge ; les propriétés inconnues peuvent être ignorées.
- Conserver les sélecteurs du menu classique et ceux du nouveau menu Cinnamon
  6.6+ ; ne pas en supprimer un parce que la version locale ne l’utilise pas.
- Toute couleur dépendant du flavor doit passer par un jeton. Ne pas copier une
  couleur de Mocha dans un autre thème ni coder une couleur en dur dans un
  asset propre à une flavor.
- Le bleu est l’accent par défaut, conformément au guide de style Catppuccin ;
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
  un texte foncé, jamais un texte clair illisible.
- Les assets SVG/PNG sont générés pour chaque flavor. Le texte des vignettes est
  volontairement simple ; ne pas dépendre d’une police externe.
- Conserver les quatre flavors, les accents configurables et les aperçus. La
  documentation et les commentaires destinés à l’utilisateur restent en
  français.

## Données et configuration à préserver

- Ne pas supprimer ni remplacer la configuration personnelle de l’utilisateur :
  `~/.themes`, `~/.local/share/themes`, les préférences Cinnamon et les fichiers
  de `~/.config` ne doivent être modifiés qu’avec un accord explicite.
- L’installateur copie les thèmes générés et remplace les dossiers
  `Catppuccin-*` présents dans la destination ; prévenir l’utilisateur avant
  toute installation réelle. Utiliser `--dest` vers un répertoire temporaire,
  `--dry-run` pour simuler ou `--backup` pour conserver l’ancienne version.
- `dist/` et `previews/` sont des artefacts générés, mais ils font partie du
  livrable et sont suivis par Git. Ne pas y ajouter de captures temporaires, de
  caches, de secrets ou de données personnelles. Les fichiers ignorés
  (`__pycache__`, `.DS_Store`) ne doivent pas être versionnés.
- La licence du code est MIT ; la palette et le guide de style Catppuccin sont
  crédités dans le README et sous licence MIT. Conserver ces attributions.

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
seconde fois avec `--accent mauve --strict-contrast` pour détecter un jeton
propre à l’accent par défaut et tout écart de contraste.

Le workflow `release.yml` est adapté au thème :
- il se déclenche sur un tag `v*` ou manuellement avec un tag en paramètre ;
- il exécute `scripts/check.sh`, donc `dist/` et `previews/` suivis doivent être
  à jour ;
- il exige que le tag existe et pointe sur le commit courant, sans jamais
  déplacer un tag ;
- il vérifie les cinq archives puis crée une release **en brouillon** intitulée
  « Catppuccin pour Cinnamon <tag> » avec
  `Catppuccin-{Latte,Frappe,Macchiato,Mocha}.zip` et
  `Catppuccin-Cinnamon-all-flavors.zip`.

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
