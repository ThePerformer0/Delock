# DeLock — Détection des verrous inutiles

Ce dépôt accompagne mon mémoire de M2 sur l'identification et l'évaluation des mécanismes d'exclusion mutuelle inutiles. Le fichier `project-description.md` décrit en détail les objectifs, les expériences prévues et la méthodologie (statique, dynamique et hybride).

## Structure prévue

- `experiments/` : jeux d'expériences A–D (race condition, mutex, lock inutile, double lock) avec code C, Makefiles et scripts d'exécution.
- `scripts/` : outils Python pour collecter et tracer les résultats.
- `docs/latex/` : brouillon du mémoire et bibliographie.
- `research-notes/` : idées, patterns et notes de travail.
- `LICENSE` : licence MIT.

## Démarrage rapide

1) Cloner le dépôt puis installer un environnement Linux (Ubuntu 20.04+ recommandé) avec `gcc`/`clang`, `make`, Python 3.8+.  
2) Consulter `project-description.md` pour le plan d’expériences et la feuille de route.
3) Aller dans `experiments/expA_race_condition`, exécuter `make` puis lancer le binaire pour vérifier la toolchain.

## État actuel

Cette version initialise seulement l’arborescence et des fichiers squelettes. Le code des expériences, des scripts et du mémoire reste à compléter dans les prochaines itérations.
