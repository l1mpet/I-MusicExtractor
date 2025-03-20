# I-MusicExtractor

A Python application for extracting metadata from audio files (MP3, M4A) and organizing them into folders with a hierarchical structure on your desktop.

## Features

- Extracts artist, title, and album metadata from MP3 and M4A files
- Creates a "Extracted Music" folder on your desktop
- Organizes audio files in a hierarchy: Artist → Album → Song
- Files without album information go into an "Unknown Album" folder within their artist folder
- Renames files based on their song title while preserving the original file format
- Handles files with missing metadata gracefully
- Detects and skips duplicate files (same artist, album, and title)
- Option to move files instead of copying them
- Optional album artwork extraction
- Web search for missing album information for songs in "Unknown Album" folders
- Intelligent album identification with scoring system to prioritize official album releases
- Automatic cleanup of empty "Unknown Album" folders
- Find and attach album art to files that lack it
- Automatically moves files from "Unknown Album" to proper album folders when adding album art
- Smart duplicate detection to prevent re-adding songs to "Unknown Album" that were previously organized into proper album folders
- Multi-source album art lookup with fallback mechanisms (Last.fm, Wikipedia, and DBpedia)
- Option to use folder structure instead of file metadata for artist/album information
- Consistent cleanup of empty "Unknown Album" folders in all operations
- **NEW: User-friendly graphical interface for easy operation on Windows and macOS**

## Requirements

- Python 3.6 or higher
- mutagen library (for audio metadata)
- Pillow library (for handling album artwork, only needed if using --extract-art)
- requests library (for web API calls to find album information)
- tkinter (included with Python for the GUI version)

## Installation

1. Clone this repository or download the files
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Graphical User Interface (GUI)

For a user-friendly experience, you can use the GUI version of I-MusicExtractor:

```bash
python I-MusicExtractor-GUI.py
```

The GUI provides easy access to all features through a tabbed interface:

1. **Main tab**: Basic operations and options
   - Set source directory and destination folder name
   - Basic options like move/copy, extract art, attach art
   - Run common operations like Extract & Organize, Find Unknown Albums, Find Album Art

2. **Advanced tab**: Additional options and operations
   - Simulation mode (dry run)
   - Keep empty folders option
   - Use folder structure option
   - Clean empty folders operation

3. **About tab**: Information about the application and its features

The GUI provides real-time console output so you can monitor the progress of operations.

### Command Line Interface (CLI)

Alternatively, you can use the command-line version:

1. Place your audio files (MP3, M4A) in the "Music_to_extract" folder in the same directory as the script
2. Run the script:

```bash
python I-MusicExtractor.py
```

#### Command Line Options

You can customize the behavior using the following options:

```bash
python I-MusicExtractor.py --move
```
This will move files instead of copying them.

```bash
python I-MusicExtractor.py -s "My Music Folder"
```
or
```bash
python I-MusicExtractor.py --source-dir "My Music Folder"
```
Specify a different source directory instead of the default "Music_to_extract". You can use either a relative path or an absolute path.

```bash
python I-MusicExtractor.py -d "My Organized Music"
```
or
```bash
python I-MusicExtractor.py --dest-name "My Organized Music"
```
Specify a different name for the destination folder on the desktop.

```bash
python I-MusicExtractor.py --extract-art
```
Enable album artwork extraction and save it as separate files (disabled by default).

```bash
python I-MusicExtractor.py --attach-art
```
Find and attach album art to file metadata during organization (requires Last.fm API key).

```bash
python I-MusicExtractor.py --force
```
Force overwrite of duplicate files and existing destination files.

```bash
python I-MusicExtractor.py --find-unknowns
```
Search for missing album information for songs in "Unknown Album" folders and reorganize them.

```bash
python I-MusicExtractor.py --find-unknowns --attach-art
```
Find missing album information and also find and attach album art for organized files.

```bash
python I-MusicExtractor.py --find-unknowns --simulate
```
Simulate the album search process without making any changes (dry run).

```bash
python I-MusicExtractor.py --keep-empty
```
Keep empty "Unknown Album" folders (by default, they are removed).

```bash
python I-MusicExtractor.py --clean-empty
```
Only clean up empty "Unknown Album" folders without processing any files.

```bash
python I-MusicExtractor.py --find-art
```
Only find and attach album art to files that don't have it in the organized structure.

```bash
python I-MusicExtractor.py --find-art --use-folders
```
Find and attach album art to files using folder structure for artist/album info instead of file metadata.

```bash
python I-MusicExtractor.py -s "/Users/username/Music/My Collection"
```
Use an absolute path to specify music files located anywhere on your system.

## Finding and Attaching Album Art

The script can search for album art online using multiple sources and attach it directly to the file's metadata:

- Use `--attach-art` during initial organization to attach album art to files as they're processed
- Use `--find-art` to scan all files in the organized structure and add album art to any that lack it
- Use `--find-unknowns --attach-art` to first find missing album information, then attach album art to all files
- Use `--use-folders` with `--find-art` to determine artist and album info from the folder structure rather than file metadata

When finding and attaching album art, the script will also:
- Identify files in "Unknown Album" folders and try to find their correct album information
- Move files from "Unknown Album" folders to proper album folders if album information is found
- Clean up empty "Unknown Album" folders after moving files (unless `--keep-empty` is specified)

The script uses a comprehensive multi-source approach for finding album artwork:

1. First tries Last.fm API (an API key is included by default)
2. If Last.fm fails, tries Wikipedia by searching for the album and extracting cover images
3. If Wikipedia fails, falls back to DBpedia semantic data to find album cover information

This multi-layered approach provides the highest chances of finding album artwork, even for obscure albums.

If you prefer to use your own Last.fm API key instead of the included one, you can set it as an environment variable:

```bash
export LASTFM_API_KEY="your_api_key_here"
```

## Finding Missing Album Information

The `--find-unknowns` option searches for songs located in "Unknown Album" folders and attempts to find their correct album information using online music databases (MusicBrainz and Last.fm). It then reorganizes these files into the proper album folders.

The script uses a sophisticated scoring system to identify the most accurate album match:
- Prioritizes high-confidence matches from MusicBrainz API (using score values)
- Favors official releases over unofficial ones
- Prefers studio albums over singles and compilations
- Avoids compilation albums when possible, as songs often appear on multiple compilations
- Falls back to Last.fm with autocorrection for better results when MusicBrainz doesn't return good matches

A Last.fm API key is included by default for the fallback API search functionality.

## Directory Structure

The script creates the following structure:

```
Extracted Music/
├── Artist A/
│   ├── Album 1/
│   │   ├── Song1.mp3
│   │   └── Song2.m4a
│   └── Album 2/
│       └── Song3.mp3
└── Artist B/
    ├── Album 3/
    │   └── Song4.mp3
    └── Unknown Album/
        └── Song5.m4a
```

With `--extract-art` option, the structure would include cover art files:

```
Extracted Music/
├── Artist A/
│   ├── Album 1/
│   │   ├── cover.jpg         # Album artwork (if available)
│   │   ├── Song1.mp3
│   │   └── Song2.m4a
...
```

## Platform Support

- Windows: Fully supported (both GUI and CLI)
- macOS: Fully supported (both GUI and CLI)
- Linux: Supported through command-line interface

## Notes

- By default, the script copies the files, so your original files remain untouched
- If album metadata is missing, the script will place the file in an "Unknown Album" folder
- Album artwork extraction (as separate files) is disabled by default; use --extract-art to enable it
- Album artwork embedding in file metadata requires --attach-art or --find-art options
- The script uses multiple online sources (Last.fm, Wikipedia, DBpedia) to find album artwork
- Empty "Unknown Album" folders are automatically cleaned up after processing (use --keep-empty to prevent this)
- The script prevents re-adding files to "Unknown Album" folders if they've already been organized into proper album folders
- Duplicate files (with same artist, album, and title) are detected and skipped
- At the end of processing, a summary of any duplicates found is displayed
- Use the --force option to override duplicate detection and overwrite existing files
- The --find-unknowns option helps organize songs that were initially placed in "Unknown Album" folders
- Web searches are rate-limited to respect the API provider's terms of service
- You can see all available options by running `python I-MusicExtractor.py --help` 