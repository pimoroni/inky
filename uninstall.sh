#!/bin/bash

PACKAGE="inky"

printf "Inky Python Library: Uninstaller\n\n"

if [ $(id -u) -ne 0 ]; then
	printf "Script must be run as root. Try 'sudo ./uninstall.sh'\n"
	exit 1
fi

cd library

printf "Unnstalling for Python 2..\n"
pip uninstall $PACKAGE

if [ -f "/usr/bin/pip3" ]; then
	printf "Uninstalling for Python 3..\n"
	pip3 uninstall $PACKAGE
fi

cd ..

printf "Done!\n"
