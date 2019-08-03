EXEC = sys-line
PREFIX = /usr/local
PYFLAGS = --onefile --name $(EXEC)
PYCC = pyinstaller

all:
	$(PYCC) $(PYFLAGS) ./$(EXEC)

clean:
	$(RM) -rv ./dist ./build ./*.spec

install: all
	@install -v ./dist/$(EXEC) $(PREFIX)/bin/$(EXEC)
