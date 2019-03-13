#!/bin/bash

printf "Inky Python Library: Installer\n\n"

if [ $(id -u) -ne 0 ]; then
	printf "Script must be run as root. Try 'sudo ./install.sh'\n"
	exit 1
fi

cd library

printf "Installing for Python 2..\n"
python setup.py install

if [ -f "/usr/bin/python3" ]; then
	printf "Installing for Python 3..\n"
	python3 setup.py install
fi

cd ..

printf "Done!\n"
