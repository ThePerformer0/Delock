#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>

static long shared_value = 0;
static pthread_mutex_t lock_a = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t lock_b = PTHREAD_MUTEX_INITIALIZER;

typedef struct {
    long iterations;
} worker_args;

void *worker(void *arg) {
    worker_args *cfg = (worker_args *)arg;
    for (long i = 0; i < cfg->iterations; ++i) {
        pthread_mutex_lock(&lock_a);
        pthread_mutex_lock(&lock_b);
        shared_value++;
        pthread_mutex_unlock(&lock_b);
        pthread_mutex_unlock(&lock_a);
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

    long expected = threads * iterations;
    printf("Final value = %ld (expected %ld) avec double verrouillage A+B\n", shared_value, expected);
    return 0;
}

