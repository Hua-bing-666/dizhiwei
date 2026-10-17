# DripGuard firmware build
#   make host    - PC replay build, verifies the whole chain today
#   make run     - build and replay a leak trajectory
# The ARM target build is not wired up: no toolchain on this machine.

CC      ?= gcc
CFLAGS  ?= -std=c99 -Wall -Wextra -Werror -O2
LDLIBS  ?= -lm
INC     := -Ibsp

HOST_SRC := app/main.c core/sampler.c bsp/bsp_host.c \
            integer_diagnosis.c protocol_v2_codec.c
HOST_BIN := build/node_host.exe

FEED_LEAK  := data/feed_leak.csv
FEED_RESTR := data/feed_restriction.csv
FEED_NORM  := data/feed_normal.csv
FEED_DRIFT := data/feed_drift.csv

.PHONY: all host run run-all clean

all: host

host: $(HOST_BIN)

$(HOST_BIN): $(HOST_SRC) bsp/bsp.h core/sampler.h
	@mkdir -p build
	$(CC) $(CFLAGS) -DBSP_HOST $(INC) -o $@ $(HOST_SRC) $(LDLIBS)

run: $(HOST_BIN)
	./$(HOST_BIN) $(FEED_LEAK) build/out_leak.csv

run-all: $(HOST_BIN)
	@mkdir -p build
	./$(HOST_BIN) $(FEED_NORM)  build/out_normal.csv
	./$(HOST_BIN) $(FEED_LEAK)  build/out_leak.csv
	./$(HOST_BIN) $(FEED_RESTR) build/out_restriction.csv
	./$(HOST_BIN) $(FEED_DRIFT) build/out_drift.csv

clean:
	rm -rf build
