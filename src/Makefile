CC = cc
CFLAGS = -Wall -Werror -pedantic -std=c99 -g
SRC = $(wildcard *.c) \
	  $(wildcard systems/*.c)
OBJ = $(SRC:.c=.o)
EXEC = sys-line

$(EXEC): $(OBJ)
	$(CC) -o $@ $^

.PHONY: clean
clean:
	$(RM) -v $(OBJ) $(EXEC)
