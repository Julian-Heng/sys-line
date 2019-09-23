CC = cc
CFLAGS = #-Wall -Werror -pedantic -std=c99 -g
SRC = $(wildcard *.c) \
	  $(wildcard utils/*.c) \
	  $(wildcard systems/*.c) \
	  $(wildcard systems/commons/*.c) \
	  $(wildcard systems/linux/*.c) \
	  $(wildcard systems/darwin/*.c) \
	  $(wildcard systems/freebsd/*.c)

OBJ = $(SRC:.c=.o)
EXEC = sys-line

$(EXEC): $(OBJ)
	$(CC) -o $@ $^

.PHONY: clean
clean:
	$(RM) -v $(OBJ) $(EXEC)
