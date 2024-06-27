#!/bin/bash
LIBRARY_NAME=$(grep -m 1 name pyproject.toml | awk -F" = " '{print substr($2,2,length($2)-2)}')
CONFIG_FILE=config.txt
CONFIG_DIR="/boot/firmware"
DATESTAMP=$(date "+%Y-%m-%d-%H-%M-%S")
CONFIG_BACKUP=false
APT_HAS_UPDATED=false
RESOURCES_TOP_DIR="$HOME/Pimoroni"
VENV_BASH_SNIPPET="$RESOURCES_TOP_DIR/auto_venv.sh"
VENV_DIR="$HOME/.virtualenvs/pimoroni"
USAGE="./install.sh (--unstable)"
POSITIONAL_ARGS=()
FORCE=false
UNSTABLE=false
PYTHON="python"
CMD_ERRORS=false


user_check() {
	if [ "$(id -u)" -eq 0 ]; then
		fatal "Script should not be run as root. Try './install.sh'\n"
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

success() {
	echo -e "$(tput setaf 2)$1$(tput sgr0)"
}

inform() {
	echo -e "$(tput setaf 6)$1$(tput sgr0)"
}

warning() {
	echo -e "$(tput setaf 1)⚠ WARNING:$(tput sgr0) $1"
}

fatal() {
	echo -e "$(tput setaf 1)⚠ FATAL:$(tput sgr0) $1"
	exit 1
}

find_config() {
	if [ ! -f "$CONFIG_DIR/$CONFIG_FILE" ]; then
		CONFIG_DIR="/boot"
		if [ ! -f "$CONFIG_DIR/$CONFIG_FILE" ]; then
			fatal "Could not find $CONFIG_FILE!"
		fi
	fi
	inform "Using $CONFIG_FILE in $CONFIG_DIR"
}

venv_bash_snippet() {
	inform "Checking for $VENV_BASH_SNIPPET\n"
	if [ ! -f "$VENV_BASH_SNIPPET" ]; then
		inform "Creating $VENV_BASH_SNIPPET\n"
		mkdir -p "$RESOURCES_TOP_DIR"
		cat << EOF > "$VENV_BASH_SNIPPET"
# Add "source $VENV_BASH_SNIPPET" to your ~/.bashrc to activate
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
	PYTHON_BIN=$(which "$PYTHON")
	if [[ $VIRTUAL_ENV == "" ]] || [[ $PYTHON_BIN != $VIRTUAL_ENV* ]]; then
		printf "This script should be run in a virtual Python environment.\n"
		if confirm "Would you like us to create and/or use a default one?"; then
			printf "\n"
			if [ ! -f "$VENV_DIR/bin/activate" ]; then
				inform "Creating a new virtual Python environment in $VENV_DIR, please wait...\n"
				mkdir -p "$VENV_DIR"
				/usr/bin/python3 -m venv "$VENV_DIR" --system-site-packages
				venv_bash_snippet
				# shellcheck disable=SC1091
				source "$VENV_DIR/bin/activate"
			else
				inform "Activating existing virtual Python environment in $VENV_DIR\n"
				printf "source \"%s/bin/activate\"\n" "$VENV_DIR"
				# shellcheck disable=SC1091
				source "$VENV_DIR/bin/activate"
			fi
		else
			printf "\n"
			fatal "Please create and/or activate a virtual Python environment and try again!\n"
		fi
	fi
	printf "\n"
}

check_for_error() {
	if [ $? -ne 0 ]; then
		CMD_ERRORS=true
		warning "^^^ 😬 previous command did not exit cleanly!"
	fi
}

function do_config_backup {
	if [ ! $CONFIG_BACKUP == true ]; then
		CONFIG_BACKUP=true
		FILENAME="config.preinstall-$LIBRARY_NAME-$DATESTAMP.txt"
		inform "Backing up $CONFIG_DIR/$CONFIG_FILE to $CONFIG_DIR/$FILENAME\n"
		sudo cp "$CONFIG_DIR/$CONFIG_FILE" "$CONFIG_DIR/$FILENAME"
		mkdir -p "$RESOURCES_TOP_DIR/config-backups/"
		cp $CONFIG_DIR/$CONFIG_FILE "$RESOURCES_TOP_DIR/config-backups/$FILENAME"
		if [ -f "$UNINSTALLER" ]; then
			echo "cp $RESOURCES_TOP_DIR/config-backups/$FILENAME $CONFIG_DIR/$CONFIG_FILE" >> "$UNINSTALLER"
		fi
	fi
}

function apt_pkg_install {
	PACKAGES_NEEDED=()
	PACKAGES_IN=("$@")
	# Check the list of packages and only run update/install if we need to
	for ((i = 0; i < ${#PACKAGES_IN[@]}; i++)); do
		PACKAGE="${PACKAGES_IN[$i]}"
		if [ "$PACKAGE" == "" ]; then continue; fi
		printf "Checking for %s\n" "$PACKAGE"
		dpkg -L "$PACKAGE" > /dev/null 2>&1
		if [ "$?" == "1" ]; then
			PACKAGES_NEEDED+=("$PACKAGE")
		fi
	done
	PACKAGES="${PACKAGES_NEEDED[*]}"
	if ! [ "$PACKAGES" == "" ]; then
		printf "\n"
		inform "Installing missing packages: $PACKAGES"
		if [ ! $APT_HAS_UPDATED ]; then
			sudo apt update
			APT_HAS_UPDATED=true
		fi
		# shellcheck disable=SC2086
		sudo apt install -y $PACKAGES
		check_for_error
		if [ -f "$UNINSTALLER" ]; then
			echo "apt uninstall -y $PACKAGES" >> "$UNINSTALLER"
		fi
	fi
}

function pip_pkg_install {
	# A null Keyring prevents pip stalling in the background
	PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring $PYTHON -m pip install --upgrade "$@"
	check_for_error
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
			printf "Unrecognised option: %s\n" "$1";
			printf "Usage: %s\n" "$USAGE";
			exit 1
		fi
		POSITIONAL_ARGS+=("$1")
		shift
	esac
done

printf "Installing %s...\n\n" "$LIBRARY_NAME"

user_check
venv_check

if [ ! -f "$(which "$PYTHON")" ]; then
	fatal "Python path %s not found!\n" "$PYTHON"
fi

PYTHON_VER=$($PYTHON --version)

inform "Checking Dependencies. Please wait..."

# Install toml and try to read pyproject.toml into bash variables

pip_pkg_install toml

CONFIG_VARS=$(
	$PYTHON - <<EOF
import toml
config = toml.load("pyproject.toml")
github_url = config['project']['urls']['GitHub']
p = dict(config['tool']['pimoroni'])
# Convert list config entries into bash arrays
for k, v in p.items():
    v = "'\n\t'".join(v)
    p[k] = f"('{v}')"
print(f'GITHUB_URL="{github_url}"')
print("""
APT_PACKAGES={apt_packages}
SETUP_CMDS={commands}
CONFIG_TXT={configtxt}
""".format(**p))
EOF
)

# shellcheck disable=SC2181 # Inlining the above command would be messy
if [ $? -ne 0 ]; then
	# This is bad, this should not happen in production!
	fatal "Error parsing configuration...\n"
fi

eval "$CONFIG_VARS"

RESOURCES_DIR=$RESOURCES_TOP_DIR/$LIBRARY_NAME
UNINSTALLER=$RESOURCES_DIR/uninstall.sh

RES_DIR_OWNER=$(stat -c "%U" "$RESOURCES_TOP_DIR")

# Previous install.sh scripts were run as root with sudo, which caused
# the ~/Pimoroni dir to be created with root ownership. Try and fix it.
if [[ "$RES_DIR_OWNER" == "root" ]]; then
	warning "\n\nFixing $RESOURCES_TOP_DIR permissions!\n\n"
	sudo chown -R "$USER:$USER" "$RESOURCES_TOP_DIR"
fi

mkdir -p "$RESOURCES_DIR"

# Create a stub uninstaller file, we'll try to add the inverse of every
# install command run to here, though it's not complete.
cat << EOF > "$UNINSTALLER"
printf "It's recommended you run these steps manually.\n"
printf "If you want to run the full script, open it in\n"
printf "an editor and remove 'exit 1' from below.\n"
exit 1
source $VIRTUAL_ENV/bin/activate
EOF

printf "\n"

inform "Installing for $PYTHON_VER...\n"

# Install apt packages from pyproject.toml / tool.pimoroni.apt_packages
apt_pkg_install "${APT_PACKAGES[@]}"

printf "\n"

if $UNSTABLE; then
	warning "Installing unstable library from source.\n"
	pip_pkg_install .
else
	inform "Installing stable library from pypi.\n"
	pip_pkg_install "$LIBRARY_NAME"
fi

# shellcheck disable=SC2181 # One of two commands run, depending on --unstable flag
if [ $? -eq 0 ]; then
	success "Done!\n"
	echo "$PYTHON -m pip uninstall $LIBRARY_NAME" >> "$UNINSTALLER"
fi

find_config

printf "\n"

# Run the setup commands from pyproject.toml / tool.pimoroni.commands

inform "Running setup commands...\n"
for ((i = 0; i < ${#SETUP_CMDS[@]}; i++)); do
	CMD="${SETUP_CMDS[$i]}"
	# Attempt to catch anything that touches config.txt and trigger a backup
	if [[ "$CMD" == *"raspi-config"* ]] || [[ "$CMD" == *"$CONFIG_DIR/$CONFIG_FILE"* ]] || [[ "$CMD" == *"\$CONFIG_DIR/\$CONFIG_FILE"* ]]; then
		do_config_backup
	fi
	if [[ ! "$CMD" == printf* ]]; then
		printf "Running: \"%s\"\n" "$CMD"
	fi
	eval "$CMD"
	check_for_error
done

printf "\n"

# Add the config.txt entries from pyproject.toml / tool.pimoroni.configtxt

for ((i = 0; i < ${#CONFIG_TXT[@]}; i++)); do
	CONFIG_LINE="${CONFIG_TXT[$i]}"
	if ! [ "$CONFIG_LINE" == "" ]; then
		do_config_backup
		inform "Adding $CONFIG_LINE to $CONFIG_DIR/$CONFIG_FILE"
		sudo sed -i "s/^#$CONFIG_LINE/$CONFIG_LINE/" $CONFIG_DIR/$CONFIG_FILE
		if ! grep -q "^$CONFIG_LINE" $CONFIG_DIR/$CONFIG_FILE; then
			printf "%s \n" "$CONFIG_LINE" | sudo tee --append $CONFIG_DIR/$CONFIG_FILE
		fi
	fi
done

printf "\n"

# Just a straight copy of the examples/ dir into ~/Pimoroni/board/examples

if [ -d "examples" ]; then
	if confirm "Would you like to copy examples to $RESOURCES_DIR?"; then
		inform "Copying examples to $RESOURCES_DIR"
		cp -r examples/ "$RESOURCES_DIR"
		echo "rm -r $RESOURCES_DIR" >> "$UNINSTALLER"
		success "Done!"
	fi
fi

printf "\n"

# Use pdoc to generate basic documentation from the installed module

if confirm "Would you like to generate documentation?"; then
	inform "Installing pdoc. Please wait..."
	pip_pkg_install pdoc
	inform "Generating documentation.\n"
	if $PYTHON -m pdoc "$LIBRARY_NAME" -o "$RESOURCES_DIR/docs" > /dev/null; then
		inform "Documentation saved to $RESOURCES_DIR/docs"
		success "Done!"
	else
		warning "Error: Failed to generate documentation."
	fi
fi

printf "\n"

if [ "$CMD_ERRORS" = true ]; then
	warning "One or more setup commands appear to have failed."
	printf "This might prevent things from working properly.\n"
	printf "Make sure your OS is up to date and try re-running this installer.\n"
	printf "If things still don't work, report this or find help at %s.\n\n" "$GITHUB_URL"
else
	success "\nAll done!"
fi

printf "If this is your first time installing you should reboot for hardware changes to take effect.\n"
printf "Find uninstall steps in %s\n\n" "$UNINSTALLER"

if [ "$CMD_ERRORS" = true ]; then
	exit 1
else
	exit 0
fi
