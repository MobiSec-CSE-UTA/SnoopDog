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

# 2.1. Check if curl is installed (needed for pip installation)
install_package "curl" "curl"

# 2.5. Install python3-venv and python3-dev packages
echo "[*] Checking for required Python packages..."

# Get Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "[*] Detected Python version: $PYTHON_VERSION"

# Install version-specific venv package
VENV_PACKAGE="python${PYTHON_VERSION}-venv"
if ! dpkg -l | grep -q "$VENV_PACKAGE"; then
    echo "[*] $VENV_PACKAGE is not installed. Installing..."
    echo "[!] This requires sudo privileges for system package installation"
    sudo apt update
    sudo apt install -y "$VENV_PACKAGE"
else
    echo "[+] $VENV_PACKAGE is already installed."
fi

# Also install python3-dev for building packages
DEV_PACKAGE="python${PYTHON_VERSION}-dev"
if ! dpkg -l | grep -q "$DEV_PACKAGE"; then
    echo "[*] $DEV_PACKAGE is not installed. Installing..."
    echo "[!] This requires sudo privileges for system package installation"
    sudo apt install -y "$DEV_PACKAGE"
else
    echo "[+] $DEV_PACKAGE is already installed."
fi

# Install distutils if needed (Ubuntu 22.04+)
DISTUTILS_PACKAGE="python${PYTHON_VERSION}-distutils"
if ! dpkg -l | grep -q "$DISTUTILS_PACKAGE" 2>/dev/null; then
    echo "[*] $DISTUTILS_PACKAGE is not installed. Installing..."
    echo "[!] This requires sudo privileges for system package installation"
    sudo apt install -y "$DISTUTILS_PACKAGE" 2>/dev/null || echo "[!] $DISTUTILS_PACKAGE not available, continuing..."
else
    echo "[+] $DISTUTILS_PACKAGE is already installed."
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
if [ -d "$VENV_NAME" ]; then
    echo "[*] Removing existing virtual environment '$VENV_NAME'..."
    rm -rf "$VENV_NAME"
fi

echo "[*] Creating virtual environment '$VENV_NAME'..."

# Try creating virtual environment with pip first
if python3 -m venv "$VENV_NAME" 2>/dev/null; then
    echo "[+] Virtual environment created successfully with pip."
    source "$VENV_NAME/bin/activate"
else
    echo "[*] Creating virtual environment without pip and installing manually..."
    python3 -m venv "$VENV_NAME" --without-pip
    source "$VENV_NAME/bin/activate"
    
    # Install pip manually in the virtual environment
    echo "[*] Installing pip in virtual environment..."
    
    # Try using curl first, then wget as fallback
    if command -v curl >/dev/null 2>&1; then
        curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    elif command -v wget >/dev/null 2>&1; then
        wget https://bootstrap.pypa.io/get-pip.py
    else
        echo "[!] Error: Neither curl nor wget is available. Cannot download pip installer."
        echo "[!] Please install curl or wget and run the script again."
        exit 1
    fi
    
    python get-pip.py
    rm get-pip.py
    echo "[+] Virtual environment created and pip installed successfully."
fi

# Verify pip installation
if ! command -v pip >/dev/null 2>&1; then
    echo "[!] Error: pip is not available in the virtual environment."
    exit 1
fi

echo "[+] Virtual environment is ready with pip."

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