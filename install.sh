#!/bin/bash

printf "Inky Python Library: Installer\n\n"

if [ $(id -u) -ne 0 ]; then
	printf "Script must be run as root. Try 'sudo ./install.sh'\n"
	exit 1
fi

function py_install() {
	if [ -f "$1" ]; then
		VERSION=`$1 --version 2>&1`
		printf "Installing for $VERSION..\n"
		$1 -m pip install --no-binary .[example-depends] ./library/
	fi
}

py_install /usr/bin/python
py_install /usr/bin/python3

printf "Done!\n"
