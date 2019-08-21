CC = cc
CFLAGS = -std=c99
SRC = $(wildcard *.c) \
	  $(wildcard systems/*.c)
OBJ = $(SRC:.c=.o)
EXEC = sys-line

$(EXEC): $(OBJ)
	$(CC) -o $@ $^

.PHONY: clean
clean:
	$(RM) $(OBJ) $(EXEC)
