LIBRARY_NAME := $(shell hatch project metadata name 2> /dev/null)
LIBRARY_VERSION := $(shell hatch version 2> /dev/null)

.PHONY: usage install uninstall check pytest qa build-deps check tag wheel sdist clean dist testdeploy deploy
usage:
ifdef LIBRARY_NAME
	@echo "Library: ${LIBRARY_NAME}"
	@echo "Version: ${LIBRARY_VERSION}\n"
else
	@echo "WARNING: You should 'make dev-deps'\n"
endif
	@echo "Usage: make <target>, where target is one of:\n"
	@echo "install:      install the library locally from source"
	@echo "uninstall:    uninstall the local library"
	@echo "dev-deps:     install Python dev dependencies"
	@echo "check:        perform basic integrity checks on the codebase"
	@echo "qa:           run linting and package QA"
	@echo "pytest:       run Python test fixtures"
	@echo "clean:        clean Python build and dist directories"
	@echo "build:        build Python distribution files"
	@echo "testdeploy:   build and upload to test PyPi"
	@echo "deploy:       build and upload to PyPi"
	@echo "tag:          tag the repository with the current version\n"

version:
	@hatch version

install:
	./install.sh --unstable

uninstall:
	./uninstall.sh

dev-deps:
	python3 -m pip install -r requirements-dev.txt
	sudo apt install dos2unix shellcheck

check:
	@bash check.sh

shellcheck:
	shellcheck *.sh

qa:
	tox -e qa

pytest:
	tox -e py

nopost:
	@bash check.sh --nopost

tag: version
	git tag -a "v${LIBRARY_VERSION}" -m "Version ${LIBRARY_VERSION}"

build: check
	@hatch build

clean:
	-rm -r dist

testdeploy: build
	twine upload --repository testpypi dist/*

deploy: nopost build
	twine upload dist/*
