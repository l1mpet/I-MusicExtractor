#!/bin/bash

echo "Installing I-MusicExtractor dependencies..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed or not in the PATH."
    echo "Please install Python 3 using your package manager:"
    echo "  macOS:   brew install python3"
    echo "  Ubuntu:  sudo apt install python3 python3-pip"
    echo "  Fedora:  sudo dnf install python3 python3-pip"
    echo
    echo "Press Enter to exit..."
    read
    exit 1
fi

# Install dependencies
echo "Installing required packages..."
pip3 install --upgrade pip
pip3 install -r requirements.txt

# Make sure the run script is executable
chmod +x run_gui.sh

echo
echo "Installation complete!"
echo
echo "You can now run the GUI by executing ./run_gui.sh or by running:"
echo "python3 I-MusicExtractor-GUI.py"
echo
echo "Press Enter to exit..."
read 