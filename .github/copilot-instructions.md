# Instructions du projet

- Lire et appliquer [AGENTS.md](../AGENTS.md), qui définit les consignes communes du dépôt.
- Maintenir la documentation exclusivement en Markdown dans le dépôt : `README.md` comme point d’entrée. Si des guides, plans ou comptes rendus sont ajoutés, les placer dans `docs/` (dossier encore inexistant), les référencer depuis `README.md`, et ne pas mettre à jour les anciennes copies Notion.
- Vérifier les modifications avec `make check` (ou `bash scripts/check.sh`), qui reconstruit les thèmes dans un répertoire temporaire et compare `dist/` et `previews/` suivis à cette compilation fraîche.
- Ne créer aucun commit, push, tag, pull request ou Release sans confirmation explicite de l’utilisateur, conformément à `AGENTS.md`.
- Distinguer contrôles statiques et recette réelle sous Cinnamon/X11.

## Génération de messages de commit

- Génère toujours les messages de commit en français.
- Le titre doit être une courte phrase résumant le changement.
- La description doit expliquer clairement la raison du changement, doit être courte et en français.
