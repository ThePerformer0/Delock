# DeLock — Détection et analyse des mécanismes d'exclusion mutuelle inutiles

(README détaillé — version expérimentale pour le repo delock-project)


## But du projet (en une phrase)

Concevoir, implémenter et évaluer des méthodes (statique, dynamique et hybrides) permettant d'identifier quand des mécanismes d'exclusion mutuelle (mutex, futex, spinlock, etc.) sont inutiles ou redondants dans du code multithread (notamment le code généré par des LLMs), et mesurer l'impact de ces verrous sur la sûreté et les performances.

## 1. Contexte scientifique — pourquoi ce problème est important

- Les verrous (mutex, spinlocks, futex, etc.) sont essentiels pour garantir la cohérence des données en présence de plusieurs threads. Mal utilisés, ils entraînent des deadlocks, des conditions de course, et des pertes de performance. Les travaux classiques montrent qu'une analyse statique peut identifier motifs dangereux dans de larges bases de code (ex. RacerX).
- Les outils dynamiques (ex. ThreadSanitizer) détectent des data races à l'exécution et fournissent des traces utiles pour le débogage des anomalies observées en runtime.
- La détection de deadlocks à grande échelle a fait l'objet d'approches dynamiques et hybrides (ex. MagicFuzzer) qui combinent filtrage statique et tests d'exécution pour confirmer les scénarios problématiques.
- Des travaux récents montrent l'intérêt d'approches spécifiques pour des constructions mémoire/les barrières (ex. OFence) ou pour reproduire/détecter dynamiquement des deadlocks à partir de traces. Ces approches offrent des méthodes et des heuristiques que nous exploiterons et adapterons.

Ces références donnent la base sur laquelle s'appuie DeLock : combiner idées d'analyse statique (pour réduire l'espace de recherche), d'analyse dynamique (pour prouver l'utilité ou non d'un verrou) et d'heuristiques/métriques quantifiables.


## 2. Définition opérationnelle : qu'est-ce qu'un lock inutile ?

On appelle **lock inutile** un mécanisme d'exclusion mutuelle présent dans le code qui n'affecte pas la sûreté fonctionnelle du programme (absence de race/violation d'invariants) pour aucun chemin d'exécution réalisable — ou bien qui protège uniquement du code local (pas de ressource partagée) — et dont la suppression n'introduit aucun comportement incorrect (mais améliore la performance).

**Remarque pratique** : la notion d'« inutilité » est relative à un modèle d'exécution (nombre de threads, scheduling, entrées). DeLock vise donc à produire des preuves (empiriques et/ou analytiques) de l'inutilité d'un lock dans des conditions raisonnablement représentatives.


## 3. Contribution attendue du projet
(Je précise qu'il s'agit d'un projet de recherche donc les attente peuvent varié en focntion des résultats observés)

1. **Catalogue de patterns typiques** où des verrous sont inutiles (exemples simples : section critique qui n'accède qu'à des variables locales ; doublons de locks ; locks insérés par LLM sans nécessité).
2. **Méthodologie d'évaluation (pipeline)** combinant :
   - analyse statique pour repérer les candidats,
   - instrumentation / fuzzing / exécution dirigée pour tester l'impact réel,
   - métriques (cf. §6) permettant de quantifier utilité vs coût.
3. **Prototype (outil)** : script / binaire capable d'analyser des fichiers C (ou un autre langage mais on verra cela par la suite) simples, d'évaluer candidates, et de produire un rapport (preuves dynamiques + score d'utilité).
4. **Expérimentations reproductibles** : corpus de programmes tests (manuels + extraits générés par LLM), scripts d'exécution, et jeux de résultats.


## 4. Approches méthodologiques (résumé technique)

Je combine trois grandes familles d'approches — chacune a ses qualités et limites (voir littérature) :

### A. Analyse statique

- **But** : filtrer l'espace de code pour proposer candidats plausibles (verrous qui semblent protéger du code non partagé, verrous imbriqués redondants, ordres de prise de lock invariants, etc.).
- **Techniques** : CFG (controle flow graph), points-to analyses, lock-graph, dataflow interprocédural inspirée de RacerX. 
- **Avantage** : large couverture sans exécution 
- **Limite** : faux positifs.

### B. Analyse dynamique / instrumentation

- **But** : exécuter le code (ou variantes instrumentées) pour trouver preuves observables que le verrou n'est pas requis (ou au contraire qu'il est nécessaire).
- **Outils** : ThreadSanitizer (détection de data races), fuzzers d'ordonnancement, techniques de replay/tracing, outils similaires à MagicFuzzer pour deadlocks. 
- **Avantage** : preuve convaincante 
- **Limite** : couverture d'exécution (on peut ne pas déclencher certains interleavings).

### C. Approches heuristiques / hybrides

- **But** : combiner A+B pour réduire faux positifs et coût d'analyse. 
- **Exemple** : appliquer un filtre statique (retirer obviously-safe locks), prioriser candidats, puis exécuter tests ciblés (fuzzing, schedule perturbation) pour valider/invalider. Des travaux récents montrent que ce couplage est efficace à l'échelle.


## 5. Métriques et critères de décision

Pour chaque verrou candidat, DeLock calculera/mesurera :

- **CorrectnessEvidence** (bool / score) : existence de traces d'exécution montrant une violation (data race, corruption, non-atomicité) si on enlève le lock (dynamique).
- **PerformanceCost** : temps d'exécution moyen avec vs sans lock ; contention (temps passé bloqué sur lock), throughput, latence.
- **RedundancyScore** : s'il existe un autre verrou protégeant la même ressource (analyse statique).
- **UsageContext** : fréquence d'accès à la section protégée, taille de la section critique (coût), effectif de threads.
- **Confidence** : combinaison (statique evidence, dynamique evidence, nombres d'exécutions, variations d'ordonnancement) donnant une confiance globale [0..1].

**Décision simple proposée** : marquer verrou potentiellement inutile si Confidence > seuil (ex. 0.8) et PerformanceCost > seuil relatif (ex. > 5% coût CPU), et aucune CorrectnessEvidence négative n'est trouvée.


## 6. Premières expérimentations (détaillées — plan reproductible)

Les premières expériences ont pour but d'illustrer, mesurer et formaliser les phénomènes de base. Chaque expérience inclut : code source, protocole d'exécution, métriques à collecter, résultats attendus.

**Organisation** : dossier `experiments/expA_race_condition/`, `expB_mutex_correctness/`, `expC_useless_lock/`, `expD_double_lock/`.

Scripts fournis pour compiler, exécuter en boucles, instrumenter avec TSan, et agréger résultats (CSV + plots).

### Expérience A — Race condition (sans lock)

**Objectif** : démontrer la non-déterminisme d'accès partagé sans protection et quantifier la perte d'intégrité.

**Code-type** : compteur global (balance), N threads effectuant M incréments (balance++) — code en C / pthreads.

**Protocoles** :
- Paramètres : threads ∈ {1,2,4,8,16,32}, itérations ∈ {10^4, 10^5, 10^6}, REPEATS = 20.
- Exécution : lancer binaire non-instrumenté et version TSan (`-fsanitize=thread`) pour confirmer races (TSan signale occurrence).

**Métriques** : final_balance vs expected, variance, taux d'échec (final != expected), temps d'exécution.

**Résultat attendu** : divergences croissantes avec nombre de threads ; TSan signale races.

### Expérience B — Correctness avec mutex (protection)
(Je penses ici que nous pouvons egalement faire les test avec les autre type de lock tel que les futex etc au moins 5 autres types)

**Objectif** : montrer que l'introduction d'un mutex corrige la race mais engendre un coût (contention).

**Code-type** : même code qu'A mais avec `pthread_mutex_lock/unlock`.

**Protocoles** :
- Mesurer temps total, temps passé bloqué (si instrumentable), throughput.
- Comparer mean_time et std entre version lockée et non-lockée.

**Métriques** : overhead percentage = (T_locked - T_unlocked) / T_unlocked * 100.

**Résultat attendu** : balance correcte ; coût temporel croissant en fonction de la contention (threads élevés).

### Expérience C — Lock inutile (cas simple)

**Objectif** : construire un cas où la section protégée ne touche aucune donnée partagée — la suppression du lock ne change rien mais réduit le temps.

**Code-type** : worker qui lock puis appelle une fonction `compute_local()` qui manipule uniquement des variables locales.

**Protocoles** :
- Exécution multiple (REPEATS) ; mesurer temps moyen avec/sans lock.
- Vérifier aucune différence fonctionnelle (assertions) ; utiliser TSan pour s'assurer qu'aucune race n'est introduite quand on enlève le lock.

**Métriques** : performance gain % ; Confidence (basée sur N runs, absence d'alerte TSan, et analyse statique montrant aucune variable partagée accédée).

**Résultat attendu** : gain significatif (dépendant taille section) ; verrou marqué « inutilisé ».

### Expérience D — Double lock / redondance

**Objectif** : détecter cas où deux verrous différents protègent la même ressource (ou mélanges où un seul suffirait).

**Code-type** : deux mutex A,B pris avant accès d'une ressource unique.

**Protocoles** :
- Comparer 3 variantes : (A+B), (A seul), (B seul).
- Mesurer correctness et temps.

**Métriques** : effect of removing one lock on correctness & performanceCost.

**Résultat attendu** : un seul lock suffit → suppression de l'autre améliore perf sans perte de correctness.


## 7. Protocole expérimental — reproductibilité

- **Environnement recommandé** : Linux (Ubuntu 20.04+), gcc 9+, Python 3.8+, matplotlib/pandas pour l'analyse. (TSan fonctionne sous Clang et GCC mais la qualité des traces varie selon versions ; ThreadSanitizer doc pour usage).
- **Scripts** :
  - Makefile par expérience (compilation),
  - `run_experiments.sh` (boucles threads / repeats),
  - `collect_results.py` (agrégation CSV → plots).
- **Instrumentation** :
  - Compiler version TSan : `gcc -fsanitize=thread -g -O1 -pthread ...` puis `./bin` → lire stderr pour rapports.
  - Logging : sauvegarder stdout/stderr par ex. `./exp > logs/out_t4_r1.log 2> logs/err_t4_r1.log`.
  - Seed / determinisme : pour fuzzing d'ordonnancement on utilisera sleeps aléatoires ou injection d'ordre; garde toujours le script d'exécution (reproductibilité).
- **Analyse** : produire `results/aggregated_summary.csv` avec colonnes (program, threads, iters, run, final_balance, time_sec, tsan_warning).

## 8. Pipeline d'analyse automatisée proposé

1. **Extraction statique** : ex: grep patterns, construire lock-graph (qui lock protège quoi), marquer candidats trivials. (inspiré de RacerX).
2. **Filtering heuristique** : retirer sections où le code accède clairement à variables non-partagées ; prioriser verrous complexes (imbriqués, multiples).
3. **Validation dynamique** : exécuter tests ciblés (TSan, fuzzing d'ordonnancement, répétitions), mesurer CorrectnessEvidence.
4. **Scoring & rapport** : générer score & preuve (logs + traces + plots).
5. **(Optionnel)** : proposer un patch (suppression du lock) et exécuter suite de tests automatisés pour confirmer régression=0.


## 9. Corpus tests et génération par LLMs

- **Corpus manuel** : exemples classiques (compteur, compte bancaire, reader/writer, exemples multi-lock).
- **Corpus réel** : extraits de petits projets open-source (avec permission/licence) pour tests.
- **Corpus LLM** : générer variantes de fonctions concurrentes avec prompts contrôlés (demander au LLM d'ajouter locks « par sécurité ») — puis appliquer DeLock pour détecter patterns caractéristiques.
- **Motivation** : montrer que LLMs ajoutent parfois des locks « par prudence » qui peuvent être inutiles ; analyser fréquence et patterns.


## 10. Outils & bibliographie minimale à consulter (départ)

Les lectures/ressources clés (que j'ai utilisées pour construire ce protocole) :

- Engler D., Ashcraft K., RacerX: Effective, static detection of race conditions and deadlocks, SOSP 2003.
- Cai Y., Chan W.K., MagicFuzzer: Scalable deadlock detection for large-scale applications, ICSE/related (2012).
- Serebryany K., ThreadSanitizer — runtime data race detector (docs & papers).
- Trace-driven dynamic deadlock detection and reproduction (paper / ACM).
- OFence: Pairing barriers to find concurrency bugs in the Linux kernel, EuroSys 2023 (barriers & heuristics).

**Remarque** : en phase d'écriture du mémoire, chaque utilisation ou paraphrase de ces travaux doit être correctement citée (BibTeX), et leurs méthodes comparées explicitement dans l'état de l'art.


## 11. Plan de travail proposé (sprints)

- **jour 1 (setup & expA)** : création repo + structure ; implémenter Exp A; scripts run_many; produire premiers plots.
- **jour 2 (expB & instrumentation)** : implémenter Exp B (mutex); compiler TSan; collecter metrics ; écrire section expérimentations.
- **jour 3 (expC & scoring)** : implémenter Exp C (lock inutile), définir RedundancyScore & Confidence ; automatiser scoring.
- **jour 4 (expD & hybrid)** : double-locks, tests LLM-generated snippets ; affiner pipeline statique→dynamique.
- **jour 5-8** : étendre corpus, écrire état de l'art détaillé, préparer article/mémoire, préparer présentation pour encadrement.


## 12. Résultats attendus et critères de succès

- Preuve expérimentale de l'existence de locks inutiles dans des cas construits et dans des extraits réels.
- Prototype fonctionnel capable de produire un rapport (candidates + preuve + métriques).
- Méthodologie validée (statique + dynamique) — réduction mesurable du nombre de faux positifs vs approche purement statique.
- Rédaction : sections expérimentations + méthode + état de l'art prêtes pour le mémoire ; possibilité de soumettre un article workshop/conference.

## 13. Éthique & bonnes pratiques

- Respecter les licences des projets utilisés comme corpus (ne pas republier sans autorisation).
- Indiquer clairement les limites : "inutilité" évaluée dans un modèle d'exécution donné ; suppression d'un lock dans un autre contexte peut être dangereuse.
- Fournir tests et scripts de reproduction pour que les résultats soient auditables.


## 14. Fichiers fournis (starter kit)

Dans le dépôt, inclure (au minimum) :

```
README.md                # (ce document)
LICENSE                  # MIT
.gitignore
docs/latex/              # draft mémoire (chapitres + references.bib)
experiments/
  expA_race_condition/
    race_no_lock.c
    Makefile
    run_many.sh
  expB_mutex_correctness/
    race_with_mutex.c
    Makefile
  expC_useless_lock/
    useless_lock.c
    Makefile
  expD_double_lock/
    double_lock.c
scripts/
  collect_results.py
  plot_results.py
research-notes/
  ideas.md
  patterns.md
```

## 15. Contact / Contribution

- **Auteur / Responsable du projet** : FEKE JIMMY WILSON
- **Repo** : github.com/ThePerformer0/Delock
- **Contributions** : issues / PR pour exemples, nouveaux patterns, jeux de tests.


## Annexes : commandes utiles de démarrage

```bash
# cloner repo (après création)
git clone git@github.com/ThePerformer0/Delock
cd Delock

# exemple : compiler et exécuter Exp A
cd experiments/expA_race_condition
make
./race_no_lock
# ou avec ThreadSanitizer (recompiler)
gcc -fsanitize=thread -g -O1 -pthread race_no_lock.c -o race_no_lock_tsan
./race_no_lock_tsan

# lancer batch runs
chmod +x run_many.sh
./run_many.sh

# analyser résultats
python3 ../../scripts/collect_results.py results/summary_timestamp.csv
```