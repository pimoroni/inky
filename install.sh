#!/bin/bash
LIBRARY_NAME=`grep -m 1 name pyproject.toml | awk -F" = " '{print substr($2,2,length($2)-2)}'`
CONFIG_FILE=config.txt
CONFIG_DIR="/boot/firmware"
DATESTAMP=`date "+%Y-%m-%d-%H-%M-%S"`
CONFIG_BACKUP=false
APT_HAS_UPDATED=false
RESOURCES_TOP_DIR=$HOME/Pimoroni
VENV_BASH_SNIPPET=$RESOURCES_DIR/auto_venv.sh
VENV_DIR=$HOME/.virtualenvs/pimoroni
WD=`pwd`
USAGE="./install.sh (--unstable)"
POSITIONAL_ARGS=()
FORCE=false
UNSTABLE=false
PYTHON="python"


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

find_config() {
	if [ ! -f "$CONFIG_DIR/$CONFIG_FILE" ]; then
		CONFIG_DIR="/boot"
		if [ ! -f "$CONFIG_DIR/$CONFIG_FILE"]; then
			warning "Could not find $CONFIG_FILE!"
			exit 1
		fi
    else
        if [ -f "/boot/$CONFIG_FILE" ] && [ ! -L "/boot/$CONFIG_FILE" ]; then
            warning "Oops! It looks like /boot/$CONFIG_FILE is not a link to $CONFIG_DIR/$CONFIG_FILE"
            warning "You might want to fix this!"
        fi
	fi
    inform "Using $CONFIG_FILE in $CONFIG_DIR"
}

venv_bash_snippet() {
	if [ ! -f $VENV_BASH_SNIPPET ]; then
		cat << EOF > $VENV_BASH_SNIPPET
# Add `source $RESOURCES_DIR/auto_venv.sh` to your ~/.bashrc to activate
# the Pimoroni virtual environment automagically!
VENV_DIR="$VENV_DIR"
if [ ! -f \$VENV_DIR/bin/activate ]; then
  printf "Creating user Python environment in \$VENV_DIR, please wait...\n"
  mkdir -p \$VENV_DIR
  python3 -m venv --system-site-packages \$VENV_DIR
fi
printf " ↓ ↓ ↓ ↓   Hello, we've activated a Python venv for you. To exit, type \"deactivate\".\n"
source \$VENV_DIR/bin/activate
EOF
	fi
}

venv_check() {
	PYTHON_BIN=`which $PYTHON`
	if [[ $VIRTUAL_ENV == "" ]] || [[ $PYTHON_BIN != $VIRTUAL_ENV* ]]; then
		printf "This script should be run in a virtual Python environment.\n"
		if confirm "Would you like us to create one for you?"; then
			if [ ! -f $VENV_DIR/bin/activate ]; then
				inform "Creating virtual Python environment in $VENV_DIR, please wait...\n"
				mkdir -p $VENV_DIR
				/usr/bin/python3 -m venv $VENV_DIR --system-site-packages
				venv_bash_snippet
			else
				inform "Found existing virtual Python environment in $VENV_DIR\n"
			fi
			inform "Activating virtual Python environment in $VENV_DIR..."
			inform "source $VENV_DIR/bin/activate\n"
			source $VENV_DIR/bin/activate

		else
			exit 1
		fi
	fi
}

function do_config_backup {
	if [ ! $CONFIG_BACKUP == true ]; then
		CONFIG_BACKUP=true
		FILENAME="config.preinstall-$LIBRARY_NAME-$DATESTAMP.txt"
		inform "Backing up $CONFIG_DIR/$CONFIG_FILE to $CONFIG_DIR/$FILENAME\n"
		sudo cp $CONFIG_DIR/$CONFIG_FILE $CONFIG_DIR/$FILENAME
		mkdir -p $RESOURCES_TOP_DIR/config-backups/
		cp $CONFIG_DIR/$CONFIG_FILE $RESOURCES_TOP_DIR/config-backups/$FILENAME
		if [ -f "$UNINSTALLER" ]; then
			echo "cp $RESOURCES_TOP_DIR/config-backups/$FILENAME $CONFIG_DIR/$CONFIG_FILE" >> $UNINSTALLER
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
			echo "apt uninstall -y $PACKAGES" >> $UNINSTALLER
		fi
	fi
}

function pip_pkg_install {
	PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring $PYTHON -m pip install --upgrade "$@"
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
venv_check

if [ ! -f `which $PYTHON` ]; then
	printf "Python path $PYTHON not found!\n"
	exit 1
fi

PYTHON_VER=`$PYTHON --version`

printf "$LIBRARY_NAME Python Library: Installer\n\n"

inform "Checking Dependencies. Please wait..."

pip_pkg_install toml

CONFIG_VARS=`$PYTHON - <<EOF
import toml
config = toml.load("pyproject.toml")
p = dict(config['tool']['pimoroni'])
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

RES_DIR_OWNER=`stat -c "%U" $RESOURCES_TOP_DIR`

if [[ "$RES_DIR_OWNER" == "root" ]]; then
	warning "\n\nFixing $RESOURCES_TOP_DIR permissions!\n\n"
	sudo chown -R $USER:$USER $RESOURCES_TOP_DIR
fi

mkdir -p $RESOURCES_DIR

cat << EOF > $UNINSTALLER
printf "It's recommended you run these steps manually.\n"
printf "If you want to run the full script, open it in\n"
printf "an editor and remove 'exit 1' from below.\n"
exit 1
source $VIRTUAL_ENV/bin/activate
EOF

if $UNSTABLE; then
	warning "Installing unstable library from source.\n\n"
else
	printf "Installing stable library from pypi.\n\n"
fi

inform "Installing for $PYTHON_VER...\n"
apt_pkg_install "${APT_PACKAGES[@]}"
if $UNSTABLE; then
	pip_pkg_install .
else
	pip_pkg_install $LIBRARY_NAME
fi
if [ $? -eq 0 ]; then
	success "Done!\n"
	echo "$PYTHON -m pip uninstall $LIBRARY_NAME" >> $UNINSTALLER
fi

cd $WD

find_config

for ((i = 0; i < ${#SETUP_CMDS[@]}; i++)); do
	CMD="${SETUP_CMDS[$i]}"
	# Attempt to catch anything that touches config.txt and trigger a backup
	if [[ "$CMD" == *"raspi-config"* ]] || [[ "$CMD" == *"$CONFIG_DIR/$CONFIG_FILE"* ]] || [[ "$CMD" == *"\$CONFIG_DIR/\$CONFIG_FILE"* ]]; then
		do_config_backup
	fi
	eval $CMD
done

for ((i = 0; i < ${#CONFIG_TXT[@]}; i++)); do
	CONFIG_LINE="${CONFIG_TXT[$i]}"
	if ! [ "$CONFIG_LINE" == "" ]; then
		do_config_backup
		inform "Adding $CONFIG_LINE to $CONFIG_DIR/$CONFIG_FILE\n"
		sudo sed -i "s/^#$CONFIG_LINE/$CONFIG_LINE/" $CONFIG_DIR/$CONFIG_FILE
		if ! grep -q "^$CONFIG_LINE" $CONFIG_DIR/$CONFIG_FILE; then
			printf "$CONFIG_LINE\n" | sudo tee --append $CONFIG_DIR/$CONFIG_FILE
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

if confirm "Would you like to generate documentation?"; then
	pip_pkg_install pdoc
	printf "Generating documentation.\n"
	$PYTHON -m pdoc $LIBRARY_NAME -o $RESOURCES_DIR/docs > /dev/null
	if [ $? -eq 0 ]; then
		inform "Documentation saved to $RESOURCES_DIR/docs"
		success "Done!"
	else
		warning "Error: Failed to generate documentation."
	fi
fi

success "\nAll done!"
inform "If this is your first time installing you should reboot for hardware changes to take effect.\n"
inform "Find uninstall steps in $UNINSTALLER\n"
