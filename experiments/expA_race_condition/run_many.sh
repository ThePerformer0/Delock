#!/usr/bin/env bash
set -euo pipefail

# Exécutions multiples pour varier le nombre de threads et d'itérations.
# Exemple : ./run_many.sh results/

out_dir="${1:-results}"
mkdir -p "$out_dir"

threads_list=("1" "2" "4" "8" "16")
iters_list=("10000" "100000")

for t in "${threads_list[@]}"; do
  for n in "${iters_list[@]}"; do
    log="${out_dir}/run_t${t}_n${n}.log"
    echo "threads=${t} iter=${n}" | tee "$log"
    ./race_no_lock "$t" "$n" | tee -a "$log"
  done
done

