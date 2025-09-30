#!/bin/bash
# filepath: d:\USB artifacts evaluation\mobisec_repo\SnoopDog\SnoopDog\install.sh

set -e  # Exit immediately on error
set -u  # Treat unset variables as an error

VENV_NAME="Snoopdog"
REQUIREMENTS_PATH="artifact/claims/claim1/requirements.txt"

echo "[*] Starting installation of requirements for SnoopDog..."

# Function to check and install system packages
install_package() {
    local package=$1
    local command_check=$2
    
    if ! command -v "$command_check" >/dev/null 2>&1; then
        echo "[*] $package is not installed. Installing $package..."
        echo "[!] This requires sudo privileges for system package installation"
        sudo apt update
        sudo apt install -y "$package"
    else
        echo "[+] $package is already installed."
    fi
}

# 1. Check if git is installed
install_package "git" "git"

# 2. Check if Python3 and pip3 are installed
install_package "python3" "python3"
install_package "python3-pip" "pip3"

# 2.5. Install python3-venv if not already installed
if ! python3 -m venv --help >/dev/null 2>&1; then
    echo "[*] python3-venv is not installed. Installing python3-venv..."
    echo "[!] This requires sudo privileges for system package installation"
    sudo apt install -y python3-venv
else
    echo "[+] python3-venv is already available."
fi

# 3. Update the current repository to latest version
echo "[*] Updating current repository to latest version..."
if [ -d ".git" ]; then
    git fetch origin
    git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || echo "[!] Could not pull from main/master branch"
    echo "[+] Repository updated successfully."
else
    echo "[!] Warning: Not in a git repository. Skipping update."
fi

# 4. Create and activate virtual environment
if [ ! -d "$VENV_NAME" ]; then
    echo "[*] Creating virtual environment '$VENV_NAME'..."
    python3 -m venv "$VENV_NAME"
else
    echo "[+] Virtual environment '$VENV_NAME' already exists."
fi

echo "[*] Activating virtual environment..."
source "$VENV_NAME/bin/activate"
echo "[+] Virtual environment activated."

# 5. Install Python packages from requirements.txt
if [ -f "$REQUIREMENTS_PATH" ]; then
    echo "[*] Installing required Python packages in virtual environment..."
    pip install --upgrade pip
    pip install -r "$REQUIREMENTS_PATH"
    echo "[+] All packages installed successfully."
else
    echo "[!] Error: requirements.txt not found at $REQUIREMENTS_PATH"
    echo "[!] Please make sure you're running this script from the SnoopDog root directory"
    exit 1
fi

echo "[✅] Installation completed successfully!"

echo ""
echo "To activate the virtual environment in the future, run:"
echo "source $VENV_NAME/bin/activate"
echo ""
echo "To deactivate the virtual environment, run:"
echo "deactivate"
echo ""
echo "For next step, please follow README.md file to finish set up SnoopDog and Host PC"
echo "Further steps require hardwares and environment set-up which are not able to be automated."