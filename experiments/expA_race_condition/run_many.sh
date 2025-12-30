#!/usr/bin/env bash
set -euo pipefail

out_dir="${1:-results}"
mkdir -p "$out_dir"

csv="${out_dir}/summary.csv"
echo "run_id,threads,iterations,amount,initial_balance,final_balance,expected,overdraws,failed_checks,time_sec" > "$csv"

threads_list=("1" "2" "4" "8" "16" "24" "32" "48")
iters_list=("10000" "100000")
amount_list=("1" "10")
repeats=5
run_id=1

for t in "${threads_list[@]}"; do
  for n in "${iters_list[@]}"; do
    for a in "${amount_list[@]}"; do
      for r in $(seq 1 $repeats); do
        echo "Running: threads=${t} iters=${n} amount=${a} repeat=${r} (run_id=${run_id})"
        
        # Passer seulement 3 arguments : threads, iterations, amount
        # Le programme calculera initial_balance automatiquement
        initial=$((t * n * a))
        out=$(./race_no_lock "$t" "$n" "$a" "$initial" "$run_id" 2>&1)
        
        # Enregistrer log complet
        echo "$out" > "${out_dir}/run_t${t}_n${n}_a${a}_r${r}.log"
        
        # Extraire la dernière ligne (CSV)
        csv_line=$(echo "$out" | tail -n1)
        echo "$csv_line" >> "$csv"
        
        run_id=$((run_id+1))
      done
    done
  done
done

echo "Done. Summary saved to $csv"