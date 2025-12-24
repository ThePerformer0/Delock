#!/usr/bin/env bash
set -euo pipefail

# Exécutions multiples pour varier le nombre de threads, d'itérations et d'amount.
# Usage : ./run_many.sh results/

out_dir="${1:-results}"
mkdir -p "$out_dir"

csv="${out_dir}/summary.csv"
# Entête CSV : run_id,threads,iterations,amount,initial_balance,final_balance,expected,overdraws,failed_checks,time_sec
echo "run_id,threads,iterations,amount,initial_balance,final_balance,expected,overdraws,failed_checks,time_sec" > "$csv"

threads_list=("1" "2" "4" "8" "16" "32" "64")
iters_list=("10000" "100000")
amount_list=("1" "10")
repeats=5
run_id=1

for t in "${threads_list[@]}"; do
  for n in "${iters_list[@]}"; do
    for a in "${amount_list[@]}"; do
      for r in $(seq 1 $repeats); do
        echo "Running: threads=${t} iters=${n} amount=${a} repeat=${r} (run_id=${run_id})"
        out=$(./race_no_lock "$t" "$n" "$a" 0 "$run_id" )
        # Enregistrer log complet
        echo "$out" > "${out_dir}/run_t${t}_n${n}_a${a}_r${r}.log"
        # La dernière ligne du binaire est la ligne CSV : on l'ajoute au résumé
        csv_line=$(echo "$out" | tail -n1)
        echo "$csv_line" >> "$csv"
        run_id=$((run_id+1))
      done
    done
  done
done

echo "Done. Summary saved to $csv"

