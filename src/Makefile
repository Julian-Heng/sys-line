CC = cc
#CFLAGS = -Wall -Werror -pedantic -std=c99 -g
CFLAGS = -Wall -Werror -std=c99 -g
SRC = $(wildcard *.c) \
	  $(wildcard utils/*.c) \
	  $(wildcard systems/*.c) \
	  $(wildcard systems/commons/*.c)
UNAME_S = $(shell uname -s)
BUILD = ./build

ifeq ($(UNAME_S),Linux)
	SRC += $(wildcard systems/linux/*.c)
endif

ifeq ($(UNAME_S),Darwin)
	SRC += $(wildcard systems/darwin/*.c)
	INC = -framework Cocoa -framework CoreAudio
endif

ifeq ($(UNAME_S),FreeBSD)
	SRC += $(wildcard systems/freebsd/*.c)
endif

OBJ = $(SRC:.c=.o)
EXEC = sys-line

$(EXEC): $(OBJ)
	mkdir -p $(BUILD)
	$(CC) $(INC) -o ./build/$@ $^

.PHONY: clean
clean:
	$(RM) -v $(OBJ) $(BUILD)/$(EXEC)
