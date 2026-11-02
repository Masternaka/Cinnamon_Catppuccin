PYTHON ?= python3
ACCENT ?= mauve

.PHONY: all build check install clean preview companions

all: build

build:
	$(PYTHON) scripts/build.py --accent $(ACCENT)

check:
	bash scripts/check.sh

install: build
	./scripts/install.sh

preview: build
	@echo "Previews generated in previews/"

companions:
	$(PYTHON) scripts/recolor_companions.py

clean:
	rm -rf dist previews
