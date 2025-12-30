import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from pathlib import Path
import argparse

# Configuration pour des graphiques de qualité publication
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['legend.fontsize'] = 10

def load_data(csv_path):
    """Charge et prépare les données.

    `csv_path` peut être un chemin (str) ou une liste de chemins vers des CSV.
    """
    # Supporter une liste de fichiers CSV
    if isinstance(csv_path, (list, tuple)):
        dfs = []
        for p in csv_path:
            if not os.path.exists(p):
                raise SystemExit(f"Fichier introuvable: {p}")
            dfs.append(pd.read_csv(p))
        df = pd.concat(dfs, ignore_index=True)
    else:
        if not os.path.exists(csv_path):
            raise SystemExit(f"Fichier introuvable: {csv_path}")
        df = pd.read_csv(csv_path)

    # Calculer les métriques dérivées
    df['error'] = df['initial_balance'] - df['final_balance']
    df['error_percent'] = (df['error'] / df['initial_balance']) * 100
    df['is_correct'] = (df['final_balance'] == df['expected'])

    return df

def plot_error_vs_threads(df, output_dir):
    """Graphique 1 : Erreur en fonction du nombre de threads"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Regrouper par threads et calculer moyenne et écart-type
    grouped = df.groupby('threads').agg({
        'error': ['mean', 'std'],
        'error_percent': ['mean', 'std']
    }).reset_index()
    
    # Graphique absolu
    ax1.errorbar(grouped['threads'], 
                 grouped['error']['mean'], 
                 yerr=grouped['error']['std'],
                 marker='o', capsize=5, capthick=2, linewidth=2,
                 label='Erreur moyenne', color='#e74c3c')
    ax1.set_xlabel('Nombre de threads')
    ax1.set_ylabel('Erreur absolue (balance perdue)')
    ax1.set_title('Impact du parallélisme sur les race conditions')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.set_xscale('log', base=2)
    
    # Graphique pourcentage
    ax2.errorbar(grouped['threads'], 
                 grouped['error_percent']['mean'], 
                 yerr=grouped['error_percent']['std'],
                 marker='s', capsize=5, capthick=2, linewidth=2,
                 label='Erreur moyenne (%)', color='#3498db')
    ax2.set_xlabel('Nombre de threads')
    ax2.set_ylabel('Erreur relative (%)')
    ax2.set_title('Pourcentage de balance perdue')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    ax2.set_xscale('log', base=2)
    ax2.axhline(y=0, color='green', linestyle='--', alpha=0.5, label='Comportement correct')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/error_vs_threads.png', dpi=300, bbox_inches='tight')
    print(f"Graphique sauvegardé : {output_dir}/error_vs_threads.png")
    plt.close()

def plot_time_vs_threads(df, output_dir):
    """Graphique 2 : Temps d'exécution vs threads"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Séparer par iterations
    for iters in sorted(df['iterations'].unique()):
        data = df[df['iterations'] == iters]
        grouped = data.groupby('threads')['time_sec'].agg(['mean', 'std']).reset_index()
        
        ax.errorbar(grouped['threads'], 
                   grouped['mean'] * 1000,  # Convertir en ms
                   yerr=grouped['std'] * 1000,
                   marker='o', capsize=4, linewidth=2,
                   label=f'{iters:,} itérations')
    
    ax.set_xlabel('Nombre de threads')
    ax.set_ylabel('Temps d\'exécution (ms)')
    ax.set_title('Performance : Temps d\'exécution moyen')
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_xscale('log', base=2)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/time_vs_threads.png', dpi=300, bbox_inches='tight')
    print(f"Graphique sauvegardé : {output_dir}/time_vs_threads.png")
    plt.close()

def plot_correctness_rate(df, output_dir):
    """Graphique 3 : Taux de succès (runs corrects)"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Calculer taux de succès par nombre de threads
    grouped = df.groupby('threads')['is_correct'].agg(['sum', 'count']).reset_index()
    grouped['success_rate'] = (grouped['sum'] / grouped['count']) * 100
    
    bars = ax.bar(grouped['threads'], grouped['success_rate'], 
                  color=['#2ecc71' if x == 100 else '#e74c3c' for x in grouped['success_rate']],
                  edgecolor='black', linewidth=1.5, alpha=0.8)
    
    ax.set_xlabel('Nombre de threads')
    ax.set_ylabel('Taux de succès (%)')
    ax.set_title('Pourcentage d\'exécutions correctes (balance finale = attendue)')
    ax.set_ylim(0, 105)
    ax.grid(True, alpha=0.3, axis='y')
    ax.axhline(y=100, color='green', linestyle='--', alpha=0.7, label='100% correct')
    ax.legend()
    
    # Ajouter les valeurs sur les barres
    for bar, rate in zip(bars, grouped['success_rate']):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{rate:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/correctness_rate.png', dpi=300, bbox_inches='tight')
    print(f"Graphique sauvegardé : {output_dir}/correctness_rate.png")
    plt.close()

def plot_heatmap(df, output_dir):
    """Graphique 4 : Heatmap erreur % (threads × iterations)"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Pivot pour heatmap
    pivot = df.groupby(['threads', 'iterations'])['error_percent'].mean().reset_index()
    pivot_table = pivot.pivot(index='iterations', columns='threads', values='error_percent')
    
    im = ax.imshow(pivot_table.values, cmap='YlOrRd', aspect='auto', interpolation='nearest')
    
    # Configurer les axes
    ax.set_xticks(range(len(pivot_table.columns)))
    ax.set_xticklabels(pivot_table.columns)
    ax.set_yticks(range(len(pivot_table.index)))
    ax.set_yticklabels([f'{int(x):,}' for x in pivot_table.index])
    
    ax.set_xlabel('Nombre de threads')
    ax.set_ylabel('Itérations par thread')
    ax.set_title('Heatmap : Pourcentage d\'erreur moyen')
    
    # Colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Erreur (%)', rotation=270, labelpad=20)
    
    # Ajouter les valeurs dans les cellules
    for i in range(len(pivot_table.index)):
        for j in range(len(pivot_table.columns)):
            val = pivot_table.values[i, j]
            text = ax.text(j, i, f'{val:.1f}%',
                          ha="center", va="center", color="black" if val < 50 else "white",
                          fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/heatmap_error.png', dpi=300, bbox_inches='tight')
    print(f"✓ Graphique sauvegardé : {output_dir}/heatmap_error.png")
    plt.close()

def generate_summary_table(df, output_dir):
    """Génère un tableau résumé en LaTeX et CSV"""
    summary = df.groupby('threads').agg({
        'error_percent': ['mean', 'std', 'min', 'max'],
        'time_sec': ['mean', 'std'],
        'is_correct': lambda x: (x.sum() / len(x)) * 100
    }).reset_index()
    
    summary.columns = ['Threads', 'Error_Mean(%)', 'Error_Std(%)', 'Error_Min(%)', 
                      'Error_Max(%)', 'Time_Mean(s)', 'Time_Std(s)', 'Success_Rate(%)']
    
    # Sauvegarder en CSV
    summary.to_csv(f'{output_dir}/summary_table.csv', index=False, float_format='%.4f')
    print(f"Tableau résumé sauvegardé : {output_dir}/summary_table.csv")
    
    return summary

def print_key_findings(df):
    """Affiche les conclusions principales"""
    print("\n" + "="*70)
    print("CONCLUSIONS PRINCIPALES - EXPÉRIENCE A")
    print("="*70 + "\n")
    
    # 1 thread (baseline)
    one_thread = df[df['threads'] == 1]
    print(f"1 thread (baseline) :")
    print(f"  - Toutes les exécutions correctes : {one_thread['is_correct'].all()}")
    print(f"  - Temps moyen : {one_thread['time_sec'].mean()*1000:.3f} ms\n")
    
    # 48 threads (pire cas)
    max_threads = df[df['threads'] == df['threads'].max()]
    print(f"{df['threads'].max()} threads (pire cas) :")
    print(f"  - Erreur moyenne : {max_threads['error_percent'].mean():.2f}%")
    print(f"  - Taux de succès : {(max_threads['is_correct'].sum()/len(max_threads))*100:.1f}%")
    print(f"  - Temps moyen : {max_threads['time_sec'].mean()*1000:.3f} ms\n")
    
    # Corrélation threads vs erreur
    corr = df.groupby('threads')['error_percent'].mean()
    print(f"Observation : L'erreur croît avec le nombre de threads")
    print(f"  - 2 threads → {corr[2]:.2f}% d'erreur")
    print(f"  - 8 threads → {corr[8]:.2f}% d'erreur")
    print(f"  - 48 threads → {corr[48]:.2f}% d'erreur\n")
    
    print("="*70 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Analyse Exp A : Race conditions")
    parser.add_argument('--csv', help='Chemin vers un CSV résumé (optionnel).')
    parser.add_argument('--results-dir', default='results', help='Dossier contenant les CSV générés (par défaut: results/).')
    parser.add_argument('--output-dir', default='analysis_results', help='Dossier de sortie pour figures et tableaux.')
    args = parser.parse_args()

    # Déterminer le(s) CSV à charger
    if args.csv:
        csv_path = args.csv
        if not os.path.exists(csv_path):
            raise SystemExit(f"Fichier introuvable: {csv_path}")
        csv_paths = csv_path
    else:
        res_dir = Path(args.results_dir)
        if not res_dir.exists():
            raise SystemExit(f"Dossier de résultats introuvable: {res_dir}")
        csv_files = sorted([str(p) for p in res_dir.glob('*.csv')])
        if not csv_files:
            raise SystemExit(f"Aucun CSV trouvé dans {res_dir}. Générer les résultats avec `./run_many.sh`.")
        if len(csv_files) == 1:
            csv_paths = csv_files[0]
        else:
            print(f"Plusieurs CSV trouvés dans {res_dir} ; je vais les concaténer :")
            for f in csv_files:
                print(f" - {f}")
            csv_paths = csv_files

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    print("\n" + "="*70)
    print("ANALYSE EXPÉRIENCE A : RACE CONDITIONS")
    print("="*70 + "\n")

    # Charger données
    print("Chargement des données...")
    df = load_data(csv_paths)
    print(f"{len(df)} runs chargés\n")

    # Génération des graphiques
    print("Génération des graphiques...\n")
    plot_error_vs_threads(df, output_dir)
    plot_time_vs_threads(df, output_dir)
    plot_correctness_rate(df, output_dir)
    plot_heatmap(df, output_dir)

    # Tableau résumé
    print("\nGénération du tableau résumé...\n")
    summary = generate_summary_table(df, output_dir)

    # Conclusions
    print_key_findings(df)

    print(f"Analyse terminée ! Résultats dans : {output_dir}/\n")

if __name__ == '__main__':
    main()