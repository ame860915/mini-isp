CC      ?= gcc
CFLAGS  ?= -O2 -std=c11 -Wall -Wextra -Werror -pedantic
CPPFLAGS += -Iinclude
LDLIBS  += -lm

SRC := $(wildcard src/*.c)
OBJ := $(SRC:src/%.c=build/%.o)
BIN := build/mini_isp_c

all: $(BIN)

$(BIN): $(OBJ)
	$(CC) $(CFLAGS) -o $@ $^ $(LDLIBS)

build/%.o: src/%.c include/isp.h | build
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@

build:
	mkdir -p build

clean:
	rm -rf build

.PHONY: all clean
