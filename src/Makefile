CC = cc
#CFLAGS = -Wall -Werror -pedantic -std=c99 -g
CFLAGS = -Wall -Werror -std=c99 -g
SRC = $(wildcard *.c) \
	  $(wildcard utils/*.c) \
	  $(wildcard systems/*.c) \
	  $(wildcard systems/commons/*.c)
UNAME_S = $(shell uname -s)

ifeq ($(UNAME_S),Linux)
	SRC += $(wildcard systems/linux/*.c)
endif

ifeq ($(UNAME_S),Darwin)
	SRC += $(wildcard systems/darwin/*.c)
endif

ifeq ($(UNAME_S),FreeBSD)
	SRC += $(wildcard systems/freebsd/*.c)
endif

OBJ = $(SRC:.c=.o)
EXEC = sys-line

$(EXEC): $(OBJ)
	$(CC) -o $@ $^

.PHONY: clean
clean:
	$(RM) -v $(OBJ) $(EXEC)
