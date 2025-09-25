#!/bin/bash

set -e  # Exit immediately on error
set -u  # Treat unset variables as an error

REPO_URL="https://github.com/MobiSec-CSE-UTA/SnoopDog.git"
REPO_DIR="SnoopDog"
VENV_NAME="Snoopdog"
REQUIREMENTS_PATH="$REPO_DIR/artifact/claims/claim1/requirements.txt"

echo "[*] Starting installation of requirements for SnoopDog..."

# 1. Check if git is installed
if ! command -v git >/dev/null 2>&1; then
    echo "[*] git is not installed. Installing git..."
    sudo apt update
    sudo apt install -y git
else
    echo "[+] git is already installed."
fi

# 2. Check if Python3 and pip3 are installed
if ! command -v python3 >/dev/null 2>&1; then
    echo "[*] python3 is not installed. Installing python3..."
    sudo apt update
    sudo apt install -y python3
else
    echo "[+] python3 is already installed."
fi

if ! command -v pip3 >/dev/null 2>&1; then
    echo "[*] pip3 is not installed. Installing pip3..."
    sudo apt install -y python3-pip
else
    echo "[+] pip3 is already installed."
fi

# 2.5. Install python3-venv if not already installed
if ! python3 -m venv --help >/dev/null 2>&1; then
    echo "[*] python3-venv is not installed. Installing python3-venv..."
    sudo apt install -y python3-venv
else
    echo "[+] python3-venv is already available."
fi

# 3. Clone the repository if it doesn't already exist
if [ ! -d "$REPO_DIR" ]; then
    echo "[*] Cloning the SnoopDog repository..."
    git clone "$REPO_URL"
else
    echo "[+] Repository directory already exists. Using existing copy."
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
    pip install -r "$REQUIREMENTS_PATH"
    echo "[+] All packages installed successfully."
else
    echo "[!] Error: requirements.txt not found at $REQUIREMENTS_PATH"
    exit 1
fi

echo "[✅] Installation completed successfully!"

echo ""
echo "To activate the virtual environment in the future, run:"
echo "source $VENV_NAME/bin/activate"
echo ""
echo "For next step, please follow README.md file to finish set up SnoopDog and Host PC"
echo "Further steps require hardwares and envionment set-up which are not able to be automated."