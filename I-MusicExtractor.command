#!/bin/bash
# I-MusicExtractor.command - Launcher for macOS
# This script allows you to double-click to run the application from Finder

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to that directory
cd "$DIR"

# Check for Python
if command -v python3 >/dev/null 2>&1; then
    # If Python3 is available, run the GUI
    echo "Launching I-MusicExtractor GUI..."
    python3 "$DIR/I-MusicExtractor-GUI.py"
else
    echo "Python 3 is not installed or not in your PATH."
    echo "Please install Python 3.6 or later from https://www.python.org/downloads/"
    # Keep the window open on error
    read -p "Press Enter to close this window..." key
fi 