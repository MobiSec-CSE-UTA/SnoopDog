#!/bin/bash

set -e  # Exit immediately on error
set -u  # Treat unset variables as an error

REPO_URL="https://github.com/MobiSec-CSE-UTA/SnoopDog.git"
REPO_DIR="SnoopDog"
REQUIREMENTS_PATH="$REPO_DIR/artifact/claims/requirements.txt"

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

# 3. Clone the repository if it doesn't already exist
if [ ! -d "$REPO_DIR" ]; then
    echo "[*] Cloning the SnoopDog repository..."
    git clone "$REPO_URL"
else
    echo "[+] Repository directory already exists. Using existing copy."
fi

# 4. Install Python packages from requirements.txt
if [ -f "$REQUIREMENTS_PATH" ]; then
    echo "[*] Installing required Python packages..."
    pip3 install -r "$REQUIREMENTS_PATH"
    echo "[+] All packages installed successfully."
else
    echo "[!] Error: requirements.txt not found at $REQUIREMENTS_PATH"
    exit 1
fi

echo "[✅] Installation completed successfully!"

echo "For next step, please follow README.md file to finish set up SnoopDog and Host PC"
echo "Further steps require hardwares and envionment set-up which are not able to be automated."
