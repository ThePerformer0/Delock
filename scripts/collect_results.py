"""Collecte et agrégation des résultats d'expériences.

Ce script est un squelette : ajoute la logique de lecture des CSV générés par
les expériences puis agrège vers un summary unique.
"""

from pathlib import Path


def collect_results(results_dir: str) -> None:
    """Parcourt un dossier de résultats et affiche les fichiers trouvés."""
    root = Path(results_dir)
    if not root.exists():
        raise SystemExit(f"Dossier introuvable: {root}")

    csv_files = sorted(root.glob("**/*.csv"))
    if not csv_files:
        print("Aucun fichier CSV à agréger pour le moment.")
        return

    print("Fichiers détectés :")
    for csv_file in csv_files:
        print(f"- {csv_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Collecte des résultats d'expériences DeLock.")
    parser.add_argument("results_dir", help="Chemin du dossier contenant les CSV.")
    args = parser.parse_args()
    collect_results(args.results_dir)

