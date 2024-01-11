#!/bin/bash

# This script handles some basic QA checks on the source

NOPOST=$1
LIBRARY_NAME=$(hatch project metadata name)
LIBRARY_VERSION=$(hatch version | awk -F "." '{print $1"."$2"."$3}')
POST_VERSION=$(hatch version | awk -F "." '{print substr($4,0,length($4))}')
TERM=${TERM:="xterm-256color"}

success() {
	echo -e "$(tput setaf 2)$1$(tput sgr0)"
}

inform() {
	echo -e "$(tput setaf 6)$1$(tput sgr0)"
}

warning() {
	echo -e "$(tput setaf 1)$1$(tput sgr0)"
}

while [[ $# -gt 0 ]]; do
	K="$1"
	case $K in
	-p|--nopost)
		NOPOST=true
		shift
		;;
	*)
		if [[ $1 == -* ]]; then
			printf "Unrecognised option: %s\n" "$1";
			exit 1
		fi
		POSITIONAL_ARGS+=("$1")
		shift
	esac
done

inform "Checking $LIBRARY_NAME $LIBRARY_VERSION\n"

inform "Checking for trailing whitespace..."
if grep -IUrn --color "[[:blank:]]$" --exclude-dir=dist --exclude-dir=.tox --exclude-dir=.git --exclude=PKG-INFO; then
    warning "Trailing whitespace found!"
    exit 1
else
    success "No trailing whitespace found."
fi
printf "\n"

inform "Checking for DOS line-endings..."
if grep -lIUrn --color $'\r' --exclude-dir=dist --exclude-dir=.tox --exclude-dir=.git --exclude=Makefile; then
    warning "DOS line-endings found!"
    exit 1
else
    success "No DOS line-endings found."
fi
printf "\n"

inform "Checking CHANGELOG.md..."
if ! grep "^${LIBRARY_VERSION}" CHANGELOG.md > /dev/null 2>&1; then
    warning "Changes missing for version ${LIBRARY_VERSION}! Please update CHANGELOG.md."
    exit 1
else
    success "Changes found for version ${LIBRARY_VERSION}."
fi
printf "\n"

inform "Checking for git tag ${LIBRARY_VERSION}..."
if ! git tag -l | grep -E "${LIBRARY_VERSION}$"; then
    warning "Missing git tag for version ${LIBRARY_VERSION}"
fi
printf "\n"

if [[ $NOPOST ]]; then
    inform "Checking for .postN on library version..."
    if [[ "$POST_VERSION" != "" ]]; then
        warning "Found .$POST_VERSION on library version."
        inform "Please only use these for testpypi releases."
        exit 1
    else
        success "OK"
    fi
fi
