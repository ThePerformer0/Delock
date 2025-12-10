# Patterns de verrous inutiles (brouillon)

- Section critique sans accès à données partagées (variables locales uniquement).
- Verrou inséré par prudence mais aucune race détectée (TSan) sur chemin réalisable.
- Double protection : mutex A puis mutex B sur la même ressource alors qu'un seul suffit.
- Lock pris mais pas nécessaire car la ressource est immuable après init (read-only).
- Locks imbriqués toujours pris dans le même ordre et couvrant les mêmes zones (redondance).

À compléter avec exemples concrets au fur et à mesure des expériences.

