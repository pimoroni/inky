LIBRARY_NAME := $(shell hatch project metadata name 2> /dev/null)
LIBRARY_VERSION := $(shell grep -m 1 '^[0-9]' CHANGELOG.md)
BUILD_VERSION := $(shell hatch version 2> /dev/null)

.PHONY: usage version install uninstall dev-deps check pre-commit qa pytest nopost tag build clean testdeploy deploy
usage:
ifdef LIBRARY_NAME
	@echo "Library: ${LIBRARY_NAME}"
	@echo "Next version: ${LIBRARY_VERSION} (from CHANGELOG.md)"
	@echo "Build version: ${BUILD_VERSION} (from the git tag)\n"
else
	@echo "WARNING: You should 'make dev-deps'\n"
endif
	@echo "Usage: make <target>, where target is one of:\n"
	@echo "install:      install the library locally from source"
	@echo "uninstall:    uninstall the local library"
	@echo "dev-deps:     install Python dev dependencies"
	@echo "check:        verify CHANGELOG.md has an entry for an untagged version"
	@echo "qa:           run package QA (check-manifest, build, twine)"
	@echo "pre-commit:   run pre-commit hooks (lint, whitespace) on all files"
	@echo "pytest:       run Python test fixtures"
	@echo "clean:        clean Python build and dist directories"
	@echo "build:        build Python distribution files"
	@echo "testdeploy:   build and upload to test PyPi"
	@echo "deploy:       build and upload to PyPi"
	@echo "tag:          tag the repository with the version from CHANGELOG.md\n"

version:
	@echo "${LIBRARY_VERSION} (next, from CHANGELOG.md)"
	@echo "${BUILD_VERSION} (build, from the git tag)"

install:
	./install.sh --unstable

uninstall:
	./uninstall.sh

dev-deps:
	python3 -m pip install --group dev
	pre-commit install

check:
	@if [ -z "${LIBRARY_VERSION}" ]; then \
		echo "No version heading at the top of CHANGELOG.md."; \
		exit 1; \
	fi
	@if git rev-parse -q --verify "refs/tags/v${LIBRARY_VERSION}" > /dev/null; then \
		echo "v${LIBRARY_VERSION} is already tagged. Add a CHANGELOG.md entry for the new version."; \
		exit 1; \
	fi
	@echo "CHANGELOG.md is ready for v${LIBRARY_VERSION}."

pre-commit:
	pre-commit run --all-files

qa:
	tox -e qa

pytest:
	tox -e py

nopost:
	@POST_VERSION=`echo "${BUILD_VERSION}" | awk -F '.' '{print $$4}'`; \
	if [ -n "$$POST_VERSION" ]; then \
		echo "Found .$$POST_VERSION on the build version; tag a release first."; \
		exit 1; \
	fi

tag: check
	git tag -a "v${LIBRARY_VERSION}" -m "Version ${LIBRARY_VERSION}"

build:
	uv build

clean:
	-rm -r dist

testdeploy: build
	twine upload --repository testpypi dist/*

deploy: nopost build
	twine upload dist/*
