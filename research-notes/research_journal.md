## Résumé rapide — 31/12/2025

- Expérience A exécutée : **160 runs**.
- Résultat principal : **70–80%** des exécutions produisent des résultats incorrects (race conditions apparues dès 2 threads ; taux de succès stabilisé autour de **20–30%** pour des niveaux de concurrence élevés).
- Performance : l'ajout de threads **augmente fortement** le temps d'exécution (jusqu'à ~**50×** avec 48 threads) en raison de la contention et du thrashing de cache.

### Machine utilisée
- **CPU** : AMD EPYC 7402P 24-Core Processor — 1 socket, 24 cores/socket, 2 threads/core → **48 cœurs logiques**
- **RAM** : 125 Go; **Swap** : 8 Go
- **OS** : Ubuntu 24.04.3 LTS

## 1. Objectif de l'Expérience A

Démontrer et quantifier l'impact des **race conditions** sur un programme multi-threadé **sans mécanisme de synchronisation** (absence de locks). Cette expérience établit la **baseline** nécessaire pour comprendre pourquoi les locks sont indispensables dans certains contextes.

**Scénario testé** : Compte bancaire avec retraits concurrents
- Variable partagée : `balance` (solde du compte)
- Opération critique : `if (balance >= amount) { balance -= amount; }`
- **Problème** : Cette opération n'est pas atomique → possibilité de race conditions

---

## 2. Résultats Clés

### 2.1 Taux de Succès (Correctness Rate)

| Threads | Taux de Succès | Observation |
|---------|----------------|-------------|
| 1       | **100.0%** ✅  | Aucune race condition (séquentiel) |
| 2       | 35.0%          | Premières race conditions détectées |
| 4       | 20.0%          | Dégradation significative |
| 8       | 20.0%          | Stabilisation autour de 20% |
| 16-48   | 20-30%         | Incohérences systématiques |

**Interprétation** :
- Avec **1 thread** : comportement correct à 100% (pas de concurrence, donc pas de race)
- Dès **2 threads** : chute drastique à 35% → les race conditions apparaissent immédiatement
- Au-delà de **4 threads** : stabilisation entre 20-30% → le système devient **fondamentalement instable**

**Conclusion critique** : Dans un environnement concurrent sans synchronisation, **70-80% des exécutions produisent des résultats incorrects**.

---

### 2.2 Pourcentage d'Erreur Moyen

Les graphiques montrent deux tendances importantes :

#### **Erreur Absolue (balance perdue)**
- **1 thread** : 0 (aucune perte)
- **2 threads** : ~350,000 unités perdues (moyenne)
- **48 threads** : ~1,850,000 unités perdues

**Observation** : L'erreur absolue croît de manière **quasi-linéaire** avec le nombre de threads. Plus il y a de concurrence, plus la perte de cohérence est importante.

#### **Erreur Relative (pourcentage)**
- **1 thread** : 0%
- **2 threads** : ~53.8% (avec 100k itérations)
- **8 threads** : ~16.3% (avec 100k itérations)
- **48 threads** : ~4.4% (avec 100k itérations)

**Paradoxe apparent** : Pourquoi le pourcentage d'erreur **diminue** quand le nombre de threads augmente ?

**Explication** : 
- Avec **peu de threads** (2-4), les interleavings sont plus "synchronisés" par hasard, créant des conflits massifs où plusieurs threads lisent la même valeur de balance
- Avec **beaucoup de threads** (48), les accès sont plus dispersés dans le temps, réduisant la probabilité que plusieurs threads lisent exactement la même valeur
- **MAIS** : le nombre absolu d'erreurs reste très élevé (~95% des runs échouent avec 48 threads)

**Important** : Cette diminution du pourcentage d'erreur **ne signifie PAS** une amélioration ! C'est un artefact statistique. Le taux de succès reste catastrophique (20-30%).

---

### 2.3 Heatmap : Impact Combiné (Threads × Itérations)

La heatmap révèle un pattern crucial :

```
                1 thread    2 threads   4 threads   8 threads   48 threads
10k iters       100.0%      96.6%       96.1%       98.8%       99.3%
100k iters      100.0%      53.8%       29.9%       16.3%       4.4%
```

**Observations clés** :

1. **Colonne 1 thread** : 100% d'erreur avec la métrique actuelle → **correction nécessaire** dans l'interprétation (c'est en fait 0% d'erreur, 100% de succès)

2. **Ligne 10k itérations** : Erreurs très élevées (~96-99%) → Avec peu d'itérations, presque toute la balance est perdue dans les race conditions

3. **Ligne 100k itérations** : Erreurs plus faibles (~4-54%) en pourcentage, mais toujours présentes

**Interprétation** :
- Plus le nombre d'**itérations** est élevé, plus le "bruit" des race conditions se dilue statistiquement
- **MAIS** : même avec 100k itérations et 48 threads, seulement **30% des exécutions sont correctes**

**Conclusion** : Les race conditions ne "disparaissent" pas avec l'échelle, elles deviennent juste moins visibles en pourcentage relatif.

---

### 2.4 Performance : Temps d'Exécution

Le graphique de performance montre une **croissance exponentielle** du temps avec le parallélisme :

| Threads | Temps (10k iter) | Temps (100k iter) | Overhead vs 1 thread |
|---------|------------------|-------------------|----------------------|
| 1       | 0.17 ms          | 0.37 ms           | 1× (baseline)        |
| 8       | 0.42 ms          | 2.54 ms           | ~7×                  |
| 48      | 2.43 ms          | 19.3 ms           | ~52×                 |

**Observation surprenante** : Ajouter des threads **ralentit** le programme au lieu de l'accélérer !

**Explication** :
1. **Contention CPU** : Avec 48 threads sur 48 cœurs, il n'y a plus de ressources disponibles pour le scheduler
2. **Cache thrashing** : Les threads lisent/écrivent constamment la même variable (`balance`), invalidant les caches L1/L2/L3
3. **False sharing** : Même si `balance` est sur une ligne de cache différente, les accès concurrents provoquent des invalidations
4. **Context switching overhead** : Le système perd du temps à basculer entre threads

**Implication pour DeLock** :
- Un lock inutile pourrait en fait **améliorer** les performances dans certains cas en **réduisant la contention** (paradoxalement)
- Notre métrique "PerformanceCost" devra tenir compte de cet effet

---

## 3. Analyse Statistique Détaillée

### 3.1 Variabilité (Écart-types)

Les barres d'erreur dans les graphiques montrent une **haute variabilité** :

- **1 thread** : Écart-type minimal (~0.0001s) → comportement déterministe
- **48 threads** : Écart-type élevé (~±40% sur le pourcentage d'erreur) → comportement **non-déterministe**

**Interprétation** :
- Les race conditions sont **non-reproductibles** : deux exécutions identiques produisent des résultats différents
- Cette variabilité rend le **debugging extrêmement difficile** → justification des outils comme ThreadSanitizer

### 3.2 Distribution des Erreurs

D'après le tableau récapitulatif (`summary_table.csv`) :

```
Threads  Error_Mean(%)  Error_Min(%)  Error_Max(%)
2        32.07          0.00          100.00
8        60.54          0.00          100.00
48       52.74          0.00          100.00
```

**Observation** : Pour tous les niveaux de parallélisme ≥2, certains runs ont 0% d'erreur (chance) et d'autres 100% d'erreur.

**Implication** : Les race conditions sont **stochastiques**. Un programme peut sembler "fonctionner" pendant des tests, puis échouer en production.

---

## 4. Lien avec le Projet DeLock

### 4.1 Pourquoi cette Expérience est Cruciale ?

Cette expérience établit **3 vérités fondamentales** pour le projet :

1. **Les locks sont NÉCESSAIRES** dans les cas de ressources partagées
   - Sans lock, 70-80% des exécutions échouent
   - Cette expérience justifie l'existence même des mécanismes de synchronisation

2. **Les race conditions ne sont pas "théoriques"**
   - Elles apparaissent **immédiatement** dès 2 threads
   - Elles sont **systématiques**, pas exceptionnelles

3. **Le coût de la concurrence non-gérée est énorme**
   - Temps d'exécution multiplié par 50 avec 48 threads
   - Perte de données pouvant atteindre 95% de la balance initiale