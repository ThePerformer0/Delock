CC=gcc
CFLAGS=-O2 -pthread
TSAN_FLAGS=-fsanitize=thread -g -O1 -pthread

BIN=double_lock
TSAN_BIN=double_lock_tsan
SRC=double_lock.c

.PHONY: all clean tsan

all: $(BIN)

$(BIN): $(SRC)
	$(CC) $(CFLAGS) $(SRC) -o $(BIN)

tsan: $(SRC)
	$(CC) $(TSAN_FLAGS) $(SRC) -o $(TSAN_BIN)

clean:
	rm -f $(BIN) $(TSAN_BIN)

