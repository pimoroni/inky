LIBRARY_NAME=$(shell grep -m 1 name pyproject.toml | awk -F" = " '{print $$2}')
LIBRARY_VERSION=$(shell grep __version__ ${LIBRARY_NAME}/__init__.py | awk -F" = " '{print substr($$2,2,length($$2)-2)}' | awk -F"." '{print $$1"."$$2"."$$3}')

.PHONY: usage install uninstall check pytest qa build-deps check tag wheel sdist clean dist testdeploy deploy
usage:
	@echo "Library: ${LIBRARY_NAME}"
	@echo "Version: ${LIBRARY_VERSION}\n"
	@echo "Usage: make <target>, where target is one of:\n"
	@echo "install:      install the library locally from source"
	@echo "uninstall:    uninstall the local library"
	@echo "build-deps:   install essential python build dependencies"
	@echo "test-deps:    install essential python test dependencies"
	@echo "check:        perform basic integrity checks on the codebase"
	@echo "qa:           run linting and package QA"
	@echo "pytest:       run python test fixtures"
	@echo "wheel:        build python .whl files for distribution"
	@echo "sdist:        build python source distribution"
	@echo "clean:        clean python build and dist directories"
	@echo "dist:         build all python distribution files"
	@echo "testdeploy:   build all and deploy to test PyPi"
	@echo "deploy:       build all and deploy to PyPi"
	@echo "tag:          tag the repository with the current version"

install:
	./install.sh --unstable

uninstall:
	./uninstall.sh

build-deps:
	python3 -m pip install build

test-deps:
	python3 -m pip install tox
	sudo apt install dos2unix

check:
	@bash check.sh

qa:
	tox -e qa

pytest:
	tox -e py

nopost:
	@bash check.sh --nopost

tag:
	git tag -a "v${LIBRARY_VERSION}" -m "Version ${LIBRARY_VERSION}"

wheel: check
	python3 -m build --wheel

sdist: check
	python3 -m build --sdist

clean:
	-rm -r dist

dist: clean wheel sdist
	ls dist

testdeploy: dist
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

deploy: nopost dist
	twine upload dist/*
