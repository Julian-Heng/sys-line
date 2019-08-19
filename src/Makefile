CC = cc
CFLAGS = -Wall -Werror -pedantic -ansi
PREFIX = /usr
BUILD = ./build
EXEC = sys-line
SOURCES := $(shell printf "%s\n" ./*.c)

build: dir $(EXEC)

clean:
	$(RM) -rv $(BUILD)


$(EXEC): $(SOURCES)
	$(CC) $(CFLAGS) -o $(BUILD)/$@ $?


dir:
	mkdir -p $(BUILD)
