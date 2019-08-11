EXEC = sys-line
PREFIX = /usr
PYFLAGS = --recurse-all \
		  --python-flag=no_site \
		  --include-package=sys_line \
		  --warn-implicit-exceptions \
		  --warn-unusual-code \
		  --plugin-enable=pylint-warnings \
		  --full-compat \
		  --show-progress \
		  --show-scons
PYCC = python3 -X utf8 -m nuitka
FILES = ./files.txt
SETUPFLAGS = --user --record $(FILES)

ifeq ($(shell uname -s),Darwin)
SETUPFLAGS += --prefix=
endif


all:
	python3 setup.py sdist bdist_wheel


compile:
	$(PYCC) $(PYFLAGS) -o $(EXEC).bin ./$(EXEC)


install:
	python3 setup.py install $(SETUPFLAGS)


install-compile:
	@if [ -e "$(EXEC).bin" ]; then \
		install -v ./$(EXEC).bin $(PREFIX)/bin/$(EXEC); \
	else \
		printf "run 'make' to build\\n"; \
	fi


uninstall:
	@if [ -e "$(FILES)" ]; then \
		while read -r file; do \
			$(RM) -v $$file; \
		done < $(FILES); \
		$(RM) -v $(FILES); \
	fi


uninstall-compile:
	@if [ -e "$(PREFIX)/bin/$(EXEC)" ]; then \
		$(RM) -v $(PREFIX)/bin/$(EXEC); \
	fi


clean:
	$(RM) -rv ./$(EXEC).bin ./$(EXEC).dist ./$(EXEC).build \
			  ./dist ./build *.egg-info $(FILES)
