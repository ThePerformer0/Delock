#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>

static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;

typedef struct {
    long iterations;
} worker_args;

static long compute_local(long x) {
    long acc = 0;
    for (long i = 0; i < x; ++i) {
        acc += (i % 3) - (i % 2);
    }
    return acc;
}

void *worker(void *arg) {
    worker_args *cfg = (worker_args *)arg;
    for (long i = 0; i < cfg->iterations; ++i) {
        pthread_mutex_lock(&lock);
        long v = compute_local(100);  // travail local uniquement
        (void)v;                      // suppression du warning
        pthread_mutex_unlock(&lock);
    }
    return NULL;
}

int main(int argc, char **argv) {
    int threads = (argc > 1) ? atoi(argv[1]) : 4;
    long iterations = (argc > 2) ? atol(argv[2]) : 50000;

    pthread_t tids[threads];
    worker_args args = {.iterations = iterations};

    for (int i = 0; i < threads; ++i) {
        if (pthread_create(&tids[i], NULL, worker, &args) != 0) {
            perror("pthread_create");
            return 1;
        }
    }

    for (int i = 0; i < threads; ++i) {
        pthread_join(tids[i], NULL);
    }

    printf("Terminé : lock autour de travail local (candidat inutile)\n");
    return 0;
}

