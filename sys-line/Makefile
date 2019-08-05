EXEC = sys-line
PREFIX = /usr/local
PYFLAGS = --recurse-all \
		  --python-flag=no_site \
		  --warn-implicit-exceptions \
		  --warn-unusual-code \
		  --plugin-enable=pylint-warnings \
		  --full-compat \
		  --show-progress \
		  --show-scons
PYCC = python3 -X utf8 -m nuitka

all:
	$(PYCC) $(PYFLAGS) -o $(EXEC).bin ./$(EXEC)


clean:
	$(RM) -rv ./$(EXEC).bin ./$(EXEC).dist ./$(EXEC).build


install: all
	@install -v ./$(EXEC).bin $(PREFIX)/bin/$(EXEC)
