import sys
import os
from cx_Freeze import setup, Executable

# Dependencies
build_exe_options = {
    "packages": ["os", "sys", "tkinter", "mutagen", "PIL", "requests", "threading", 
                 "pathlib", "io", "contextlib", "time", "json", "shutil"],
    "excludes": ["tkinter.test"],
    "include_files": ["music_icon.ico", "music_icon.png", "README.md"],
    "include_msvcr": True,
}

# Create base executable
base = None
if sys.platform == "win32":
    base = "Win32GUI"  # Use this to hide the console window for GUI apps

# Create executables
executables = [
    Executable(
        "I-MusicExtractor-GUI.py",
        base=base,
        target_name="I-MusicExtractor.exe",
        icon="music_icon.ico",
        shortcut_name="I-MusicExtractor",
        shortcut_dir="DesktopFolder",
        copyright="Copyright © 2023",
    ),
    # Also include the CLI version
    Executable(
        "I-MusicExtractor.py",
        base=None,  # Keep the console for the CLI version
        target_name="I-MusicExtractor-CLI.exe",
        icon="music_icon.ico",
        copyright="Copyright © 2023",
    )
]

setup(
    name="I-MusicExtractor",
    version="1.0.0",
    description="Music Extraction and Organization Tool",
    author="I-MusicExtractor Team",
    options={"build_exe": build_exe_options},
    executables=executables,
)

print("To build executable, run:")
print("python setup_windows.py build")
print("\nThis will create executables in the build directory.") 