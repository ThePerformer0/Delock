CC=gcc
CFLAGS=-O2 -pthread
TSAN_FLAGS=-fsanitize=thread -g -O1 -pthread

BIN=race_with_mutex
TSAN_BIN=race_with_mutex_tsan
SRC=race_with_mutex.c

.PHONY: all clean tsan

all: $(BIN)

$(BIN): $(SRC)
	$(CC) $(CFLAGS) $(SRC) -o $(BIN)

tsan: $(SRC)
	$(CC) $(TSAN_FLAGS) $(SRC) -o $(TSAN_BIN)

clean:
	rm -f $(BIN) $(TSAN_BIN)

