CC = cc
CFLAGS = -Wall -Werror -pedantic -std=c99
INC = -framework Cocoa -framework CoreAudio
PREFIX = /usr/local
BUILD = ./build
EXEC = vol
SOURCES := $(shell printf "%s\n" ./*.c)

build: dir $(EXEC)

clean:
	$(RM) -rv $(BUILD)

$(EXEC): vol.c
	$(CC) $(CFLAGS) $(INC) -o $(BUILD)/$@ $?

install: $(EXEC)
	@install -v $(BUILD)/$(EXEC) $(PREFIX)/bin/$(EXEC)

uninstall: $(EXEC)
	$(RM) $(PREFIX)/bin/$(EXEC)

dir:
	mkdir -p $(BUILD)
