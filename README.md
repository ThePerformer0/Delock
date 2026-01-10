# DeLock — Détection et évaluation des verrous inutiles

**DeLock** est un projet de recherche visant à identifier et évaluer des mécanismes d'exclusion mutuelle (mutex, spinlocks, futex, ...) potentiellement inutiles ou redondants dans du code multithread. Le dépôt contient des prototypes d'expériences (C), des scripts d'automatisation et des notes de recherche pour construire un pipeline statique + dynamique d'analyse.

---

## ⚙️ État actuel (brève analyse)

- Expériences A–D fournies : chacune contient code C et Makefile (voir `experiments/`).
  - `expA_race_condition/` : scénario « compte bancaire » + script `run_many.sh` qui produit `results/summary.csv`.
  - `expB_mutex_correctness/`, `expC_useless_lock/`, `expD_double_lock/` : exemples complémentaires (protection par mutex, lock inutile, double-lock).
- `scripts/` contient des squelettes : `collect_results.py` (agrégation CSV) et `plot_results.py` (tracé, encore à implémenter).
- `project-description.md` documente en détail la méthodologie, le protocole expérimental et le plan de travail.

> Conclusion rapide : le squelette est fonctionnel et permet d'exécuter des expériences de base. Les prochains efforts portent sur l'automatisation des analyses (collecte, graphiques), l'amélioration du pipeline d'évaluation et l'ajout d'une CI & documentation détaillée.

---

## 🚀 Démarrage rapide

Prérequis : Linux (Ubuntu 20.04+ recommandé) ou WSL, `gcc`/`clang`, `make`, Python 3.8+, `pip` (pour dépendances futures).

1. Cloner le dépôt :

   ```bash
   git clone git@github.com:ThePerformer0/Delock.git
   cd Delock
   ```

2. Expérience A (exemple complet) :

   ```bash
   cd experiments/expA_race_condition
   make
   ./race_no_lock      # exécution simple
   ./run_many.sh       # lancer une série d'expériences -> results/summary.csv
   ```

3. Agréger / tracer résultats :

   ```bash
   python3 ../scripts/collect_results.py experiments/expA_race_condition/results
   python3 ../scripts/plot_results.py experiments/expA_race_condition/results/summary.csv output_figs/
   ```

---

## 📁 Structure du dépôt

- `experiments/` : expériences A–D (code, Makefiles, scripts d'exécution, résultats).
- `scripts/` : outils Python pour agrégation et visualisation (à compléter).
- `docs/latex/` : brouillon du mémoire et bibliographie.
- `research-notes/` : idées et patterns observés.
- `LICENSE` : MIT.

---

## Contribuer

Contributions bienvenues : issues, PRs pour nouveaux cas d'expériences, amélioration des scripts d'analyse, ou suggestions pour la méthodologie. Merci d'ouvrir une issue avant une PR majeure.

---

## Contact & auteur

- **Auteur** : FEKE JIMMY WILSON
- **Repo** : https://github.com/ThePerformer0/Delock

---

## Licence

Ce projet est distribué sous licence **MIT**. Voir le fichier `LICENSE`.
