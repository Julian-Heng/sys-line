CC = cc
CFLAGS = -g -std=c99
SRC = $(wildcard *.c) \
	  $(wildcard systems/*.c)
OBJ = $(SRC:.c=.o)
EXEC = sys-line

$(EXEC): $(OBJ)
	$(CC) -o $@ $^

.PHONY: clean
clean:
	$(RM) -v $(OBJ) $(EXEC)
