#!/usr/bin/env python3
"""
I-MusicExtractor Launcher
A simple launcher for the I-MusicExtractor GUI application.
"""
import os
import sys
import platform
import subprocess

def main():
    print("Launching I-MusicExtractor GUI...")
    
    # Get the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the script directory
    os.chdir(script_dir)
    
    # Check if Python is available
    python_cmd = "python3"
    if platform.system() == "Windows":
        # On Windows, try 'python' first, then 'py'
        try:
            subprocess.run(["python", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            python_cmd = "python"
        except FileNotFoundError:
            try:
                subprocess.run(["py", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                python_cmd = "py"
            except FileNotFoundError:
                print("Error: Python is not found. Please install Python 3.6 or later.")
                sys.exit(1)
    
    # Run the GUI script
    gui_script = os.path.join(script_dir, "I-MusicExtractor-GUI.py")
    
    try:
        # Make the script executable (for Unix-like systems)
        if platform.system() != "Windows":
            os.chmod(gui_script, 0o755)
        
        # Start the GUI
        subprocess.run([python_cmd, gui_script])
    except Exception as e:
        print(f"Error launching the application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 