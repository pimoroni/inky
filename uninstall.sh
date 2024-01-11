#!/bin/bash

FORCE=false
LIBRARY_NAME=$(grep -m 1 name pyproject.toml | awk -F" = " '{print substr($2,2,length($2)-2)}')
RESOURCES_DIR=$HOME/Pimoroni/$LIBRARY_NAME
PYTHON="python"


venv_check() {
	PYTHON_BIN=$(which $PYTHON)
	if [[ $VIRTUAL_ENV == "" ]] || [[ $PYTHON_BIN != $VIRTUAL_ENV* ]]; then
		printf "This script should be run in a virtual Python environment.\n"
		exit 1
	fi
}

user_check() {
	if [ "$(id -u)" -eq 0 ]; then
		printf "Script should not be run as root. Try './uninstall.sh'\n"
		exit 1
	fi
}

confirm() {
	if $FORCE; then
		true
	else
		read -r -p "$1 [y/N] " response < /dev/tty
		if [[ $response =~ ^(yes|y|Y)$ ]]; then
			true
		else
			false
		fi
	fi
}

prompt() {
	read -r -p "$1 [y/N] " response < /dev/tty
	if [[ $response =~ ^(yes|y|Y)$ ]]; then
		true
	else
		false
	fi
}

success() {
	echo -e "$(tput setaf 2)$1$(tput sgr0)"
}

inform() {
	echo -e "$(tput setaf 6)$1$(tput sgr0)"
}

warning() {
	echo -e "$(tput setaf 1)$1$(tput sgr0)"
}

printf "%s Python Library: Uninstaller\n\n" "$LIBRARY_NAME"

user_check
venv_check

printf "Uninstalling for Python 3...\n"
$PYTHON -m pip uninstall "$LIBRARY_NAME"

if [ -d "$RESOURCES_DIR" ]; then
	if confirm "Would you like to delete $RESOURCES_DIR?"; then
		rm -r "$RESOURCES_DIR"
	fi
fi

printf "Done!\n"
