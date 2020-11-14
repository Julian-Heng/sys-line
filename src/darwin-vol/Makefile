# sys-line - a simple status line generator
# Copyright (C) 2019-2020  Julian Heng
#
# This file is part of sys-line.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
