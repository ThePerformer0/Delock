"""Génère des graphiques à partir des CSV agrégés (placeholder).

Implémente ultérieurement : lecture du summary CSV, tracés matplotlib (temps,
throughput, variance), export en PNG/PDF.
"""

from pathlib import Path


def plot_summary(summary_csv: str, output_dir: str) -> None:
    root = Path(summary_csv)
    if not root.exists():
        raise SystemExit(f"Fichier introuvable: {root}")
    print(f"[TODO] Charger {root} et produire des figures dans {output_dir}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Tracé des résultats DeLock.")
    parser.add_argument("summary_csv", help="CSV agrégé en entrée.")
    parser.add_argument("output_dir", help="Dossier de sortie pour les figures.")
    args = parser.parse_args()
    plot_summary(args.summary_csv, args.output_dir)

