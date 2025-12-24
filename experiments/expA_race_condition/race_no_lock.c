#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdatomic.h>
#include <time.h>

// Scénario banque : solde partagé, retraits concurrents sans verrou.
static long balance = 0;
static atomic_long overdraw_count = 0;   // nombre de fois où on passe sous zéro
static atomic_long failed_check = 0;     // nombre de fois où le solde était insuffisant au test

typedef struct {
    long iterations;
    long amount;
} worker_args;

void *worker(void *arg) {
    worker_args *cfg = (worker_args *)arg;
    for (long i = 0; i < cfg->iterations; ++i) {
        // Condition de retrait sans synchronisation : race intentionnelle
        if (balance >= cfg->amount) {
            balance -= cfg->amount;  // accès non protégé → potentielle perte de cohérence
            if (balance < 0) {
                atomic_fetch_add_explicit(&overdraw_count, 1, memory_order_relaxed);
            }
        } else {
            atomic_fetch_add_explicit(&failed_check, 1, memory_order_relaxed);
        }
    }
    return NULL;
}

int main(int argc, char **argv) {
    int threads = (argc > 1) ? atoi(argv[1]) : 8;
    long iterations = (argc > 2) ? atol(argv[2]) : 100000;
    long amount = (argc > 3) ? atol(argv[3]) : 10;
    long initial_balance = (argc > 4) ? atol(argv[4]) : threads * iterations * amount;  // solde pour viser 0 attendu
    int run_id = (argc > 5) ? atoi(argv[5]) : 0; // identifiant de run pour CSV

    balance = initial_balance;

    struct timespec tstart, tend;
    clock_gettime(CLOCK_MONOTONIC, &tstart);

    pthread_t tids[threads];
    worker_args args = {.iterations = iterations, .amount = amount};

    for (int i = 0; i < threads; ++i) {
        if (pthread_create(&tids[i], NULL, worker, &args) != 0) {
            perror("pthread_create");
            return 1;
        }
    }

    for (int i = 0; i < threads; ++i) {
        pthread_join(tids[i], NULL);
    }

    clock_gettime(CLOCK_MONOTONIC, &tend);
    double elapsed = (tend.tv_sec - tstart.tv_sec) + (tend.tv_nsec - tstart.tv_nsec) / 1e9;

    long expected = initial_balance - threads * iterations * amount;
    long overdraws = atomic_load_explicit(&overdraw_count, memory_order_relaxed);
    long failed = atomic_load_explicit(&failed_check, memory_order_relaxed);

    // Message lisible pour logs humains
    printf("Solde final = %ld (attendu %ld) | overdrafts=%ld | refus=%ld | time=%.6f\n",
           balance, expected, overdraws, failed, elapsed);

    // Ligne CSV (dernière ligne) : run_id,threads,iterations,amount,initial_balance,final_balance,expected,overdraws,failed_checks,time_sec
    printf("%d,%d,%ld,%ld,%ld,%ld,%ld,%ld,%.6f\n",
           run_id, threads, iterations, amount, initial_balance, balance, expected, overdraws, failed, elapsed);

    // Retourne 0 même en présence d'incohérences pour faciliter les runs batch
    return 0;
}

