CC ?= cc
CFLAGS ?= -std=c99 -Wall -Wextra -Werror -O2
BUILD_DIR := build
TARGET := $(BUILD_DIR)/tec_mvp
SRC := src/main.c

.PHONY: all clean run

all: $(TARGET)

$(TARGET): $(SRC)
	mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) -Iinclude $(SRC) -o $(TARGET)

run: $(TARGET)
	$(TARGET)

clean:
	rm -rf $(BUILD_DIR)

