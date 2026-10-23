PYTHON ?= python3
ACCENT ?= blue

.PHONY: all build check install clean preview

all: build

build:
	$(PYTHON) scripts/build.py --accent $(ACCENT)

check:
	bash scripts/check.sh

install: build
	./scripts/install.sh

preview: build
	@echo "Previews generated in previews/"

clean:
	rm -rf dist previews
