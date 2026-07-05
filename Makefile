LIBRARY_NAME := $(shell hatch project metadata name 2> /dev/null)
LIBRARY_VERSION := $(shell hatch version 2> /dev/null)

.PHONY: usage version install uninstall dev-deps check pre-commit qa pytest nopost tag build clean testdeploy deploy
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
	@echo "check:        verify CHANGELOG.md has an entry for the current version"
	@echo "qa:           run package QA (check-manifest, build, twine)"
	@echo "pre-commit:   run pre-commit hooks (lint, whitespace) on all files"
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
	python3 -m pip install --group dev
	pre-commit install

check:
	@LIBRARY_VERSION=`hatch version | awk -F '.' '{print $$1"."$$2"."$$3}'`; \
	if grep -q "^$$LIBRARY_VERSION" CHANGELOG.md; then \
		echo "Changes found for version $$LIBRARY_VERSION."; \
	else \
		echo "Changes missing for version $$LIBRARY_VERSION! Please update CHANGELOG.md."; \
		exit 1; \
	fi

pre-commit:
	pre-commit run --all-files

qa:
	tox -e qa

pytest:
	tox -e py

nopost:
	@POST_VERSION=`hatch version | awk -F '.' '{print $$4}'`; \
	if [ -n "$$POST_VERSION" ]; then \
		echo "Found .$$POST_VERSION on library version; only use these for testpypi releases."; \
		exit 1; \
	fi

tag: version
	git tag -a "v${LIBRARY_VERSION}" -m "Version ${LIBRARY_VERSION}"

build: check
	uv build

clean:
	-rm -r dist

testdeploy: build
	twine upload --repository testpypi dist/*

deploy: nopost build
	twine upload dist/*
