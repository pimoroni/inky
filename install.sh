#!/bin/bash
LIBRARY_NAME=`grep -m 1 name pyproject.toml | awk -F" = " '{print substr($2,2,length($2)-2)}'`
LIBRARY_VERSION=`grep __version__ $LIBRARY_NAME/__init__.py | awk -F" = " '{print substr($2,2,length($2)-2)}'`
CONFIG=/boot/config.txt
DATESTAMP=`date "+%Y-%m-%d-%H-%M-%S"`
CONFIG_BACKUP=false
APT_HAS_UPDATED=false
RESOURCES_TOP_DIR=$HOME/Pimoroni
WD=`pwd`
USAGE="sudo ./install.sh (--unstable)"
POSITIONAL_ARGS=()
FORCE=false
UNSTABLE=false
PYTHON="/usr/bin/python3"


user_check() {
	if [ $(id -u) -eq 0 ]; then
		printf "Script should not be run as root. Try './install.sh'\n"
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

function do_config_backup {
	if [ ! $CONFIG_BACKUP == true ]; then
		CONFIG_BACKUP=true
		FILENAME="config.preinstall-$LIBRARY_NAME-$DATESTAMP.txt"
		inform "Backing up $CONFIG to /boot/$FILENAME\n"
		cp $CONFIG /boot/$FILENAME
		mkdir -p $RESOURCES_TOP_DIR/config-backups/
		cp $CONFIG $RESOURCES_TOP_DIR/config-backups/$FILENAME
		if [ -f "$UNINSTALLER" ]; then
			echo "cp $RESOURCES_TOP_DIR/config-backups/$FILENAME $CONFIG" >> $UNINSTALLER
		fi
	fi
}

function apt_pkg_install {
	PACKAGES=()
	PACKAGES_IN=("$@")
	for ((i = 0; i < ${#PACKAGES_IN[@]}; i++)); do
		PACKAGE="${PACKAGES_IN[$i]}"
		if [ "$PACKAGE" == "" ]; then continue; fi
		printf "Checking for $PACKAGE\n"
		dpkg -L $PACKAGE > /dev/null 2>&1
		if [ "$?" == "1" ]; then
			PACKAGES+=("$PACKAGE")
		fi
	done
	PACKAGES="${PACKAGES[@]}"
	if ! [ "$PACKAGES" == "" ]; then
		echo "Installing missing packages: $PACKAGES"
		if [ ! $APT_HAS_UPDATED ]; then
			sudo apt update
			APT_HAS_UPDATED=true
		fi
		sudo apt install -y $PACKAGES
		if [ -f "$UNINSTALLER" ]; then
			echo "apt uninstall -y $PACKAGES"
		fi
	fi
}

while [[ $# -gt 0 ]]; do
	K="$1"
	case $K in
	-u|--unstable)
		UNSTABLE=true
		shift
		;;
	-f|--force)
		FORCE=true
		shift
		;;
	-p|--python)
		PYTHON=$2
		shift
		shift
		;;
	*)
		if [[ $1 == -* ]]; then
			printf "Unrecognised option: $1\n";
			printf "Usage: $USAGE\n";
			exit 1
		fi
		POSITIONAL_ARGS+=("$1")
		shift
	esac
done

user_check

if [ ! -f "$PYTHON" ]; then
	printf "Python path $PYTHON not found!\n"
	exit 1
fi

PYTHON_VER=`$PYTHON --version`

printf "$LIBRARY_NAME ($LIBRARY_VERSION) Python Library: Installer\n\n"

inform "Checking Dependencies. Please wait..."

$PYTHON -m pip install --upgrade toml

CONFIG_VARS=`$PYTHON - <<EOF
import toml
config = toml.load("pyproject.toml")
p = dict(config['pimoroni'])
# Convert list config entries into bash arrays
for k, v in p.items():
    v = "'\n\t'".join(v)
    p[k] = f"('{v}')"
print("""
APT_PACKAGES={apt_packages}
SETUP_CMDS={commands}
CONFIG_TXT={configtxt}
""".format(**p))
EOF`

if [ $? -ne 0 ]; then
	warning "Error parsing configuration...\n"
	exit 1
fi

eval $CONFIG_VARS

RESOURCES_DIR=$RESOURCES_TOP_DIR/$LIBRARY_NAME
UNINSTALLER=$RESOURCES_DIR/uninstall.sh

mkdir -p $RESOURCES_DIR

cat << EOF > $UNINSTALLER
printf "It's recommended you run these steps manually.\n"
printf "If you want to run the full script, open it in\n"
printf "an editor and remove 'exit 1' from below.\n"
exit 1
EOF

if $UNSTABLE; then
	warning "Installing unstable library from source.\n\n"
else
	printf "Installing stable library from pypi.\n\n"
fi

inform "Installing for $PYTHON_VER...\n"
apt_pkg_install "${APT_PACKAGES[@]}"
if $UNSTABLE; then
	$PYTHON -m pip install .
else
	$PYTHON -m pip install --upgrade $LIBRARY_NAME
fi
if [ $? -eq 0 ]; then
	success "Done!\n"
	echo "$PYTHON -m pip uninstall $LIBRARY_NAME" >> $UNINSTALLER
fi

cd $WD

for ((i = 0; i < ${#SETUP_CMDS[@]}; i++)); do
	CMD="${SETUP_CMDS[$i]}"
	# Attempt to catch anything that touches /boot/config.txt and trigger a backup
	if [[ "$CMD" == *"raspi-config"* ]] || [[ "$CMD" == *"$CONFIG"* ]] || [[ "$CMD" == *"\$CONFIG"* ]]; then
		do_config_backup
	fi
	eval $CMD
done

for ((i = 0; i < ${#CONFIG_TXT[@]}; i++)); do
	CONFIG_LINE="${CONFIG_TXT[$i]}"
	if ! [ "$CONFIG_LINE" == "" ]; then
		do_config_backup
		inform "Adding $CONFIG_LINE to $CONFIG\n"
		sed -i "s/^#$CONFIG_LINE/$CONFIG_LINE/" $CONFIG
		if ! grep -q "^$CONFIG_LINE" $CONFIG; then
			printf "$CONFIG_LINE\n" >> $CONFIG
		fi
	fi
done

if [ -d "examples" ]; then
	if confirm "Would you like to copy examples to $RESOURCES_DIR?"; then
		inform "Copying examples to $RESOURCES_DIR"
		cp -r examples/ $RESOURCES_DIR
		echo "rm -r $RESOURCES_DIR" >> $UNINSTALLER
		success "Done!"
	fi
fi

printf "\n"

if [ -f "/usr/bin/pydoc" ]; then
	printf "Generating documentation.\n"
	pydoc -w $LIBRARY_NAME > /dev/null
	if [ -f "$LIBRARY_NAME.html" ]; then
		cp $LIBRARY_NAME.html $RESOURCES_DIR/docs.html
		rm -f $LIBRARY_NAME.html
		inform "Documentation saved to $RESOURCES_DIR/docs.html"
		success "Done!"
	else
		warning "Error: Failed to generate documentation."
	fi
fi

success "\nAll done!"
inform "If this is your first time installing you should reboot for hardware changes to take effect.\n"
inform "Find uninstall steps in $UNINSTALLER\n"
