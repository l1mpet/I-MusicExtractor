#!/usr/bin/env python3
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
from pathlib import Path
import importlib.util
import io
from contextlib import redirect_stdout, redirect_stderr
import shutil
import time

# Import functions from main script
try:
    # Use importlib to handle the hyphen in the filename
    spec = importlib.util.spec_from_file_location("music_extractor", "I-MusicExtractor.py")
    music_extractor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(music_extractor)
    
    # Import necessary functions
    main_function = music_extractor.main
    find_and_organize_unknowns = music_extractor.find_and_organize_unknowns
    find_and_attach_album_art = music_extractor.find_and_attach_album_art
    clean_empty_unknown_album_folders = music_extractor.clean_empty_unknown_album_folders
except Exception as e:
    print(f"Error importing from I-MusicExtractor.py: {e}")
    print("Make sure I-MusicExtractor.py is in the same directory as this script.")
    sys.exit(1)

class RedirectText:
    """Class to redirect stdout/stderr to a tkinter Text widget"""
    def __init__(self, text_widget, incremental=False):
        self.text_widget = text_widget
        self.buffer = io.StringIO()
        self.update_pending = False
        self.last_update = 0
        self.incremental = incremental
        self.last_line = ""
        
    def write(self, string):
        self.buffer.write(string)
        
        # Handle incremental updates if enabled
        if self.incremental and string.strip():
            current_time = time.time()
            if not self.update_pending and current_time - self.last_update > 0.05:  # Update at most every 50ms
                self.text_widget.after(10, self.incremental_update)
                self.update_pending = True
        # Otherwise, use batched updates
        elif not self.incremental:
            current_time = time.time()
            if not self.update_pending and current_time - self.last_update > 0.1:  # Update at most every 100ms
                self.text_widget.after(10, self.update_text_widget)
                self.update_pending = True
    
    def incremental_update(self):
        """Append only new content to the text widget"""
        try:
            self.text_widget.config(state=tk.NORMAL)
            
            # Get the buffer content
            content = self.buffer.getvalue()
            
            # Determine what's new since last update
            lines = content.splitlines()
            if not lines:
                return
                
            # Find the last line that's been displayed
            last_displayed_index = -1
            for i, line in enumerate(lines):
                if line == self.last_line:
                    last_displayed_index = i
                    break
            
            # Append new lines
            new_lines = lines[last_displayed_index + 1:]
            if new_lines:
                for line in new_lines:
                    self.text_widget.insert(tk.END, line + "\n")
                self.last_line = new_lines[-1]
                
            # Auto-scroll to the end
            self.text_widget.see(tk.END)
        finally:
            self.text_widget.config(state=tk.DISABLED)
            self.update_pending = False
            self.last_update = time.time()
    
    def update_text_widget(self):
        """Replace entire content of the text widget"""
        try:
            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.insert(tk.END, self.buffer.getvalue())
            self.text_widget.see(tk.END)  # Auto-scroll to the end
        finally:
            self.text_widget.config(state=tk.DISABLED)
            self.update_pending = False
            self.last_update = time.time()
    
    def flush(self):
        if self.buffer.getvalue():
            if self.incremental:
                self.text_widget.after(10, self.incremental_update)
            else:
                self.text_widget.after(10, self.update_text_widget)

class MusicExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("I-MusicExtractor")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)  # Set minimum window size
        
        # Initialize variables for paths
        self.source_dir = tk.StringVar(value="Music_to_extract")
        self.dest_name = tk.StringVar(value="Extracted Music")
        
        # Caches for improving performance
        self.art_cache = {}  # Cache for album art
        self.album_info_cache = {}  # Cache for album information
        
        # Set icon if available (platform-specific)
        try:
            if os.name == 'nt':  # Windows
                self.root.iconbitmap('music_icon.ico')
            else:  # macOS and Linux
                img = tk.PhotoImage(file='music_icon.png')
                self.root.tk.call('wm', 'iconphoto', self.root._w, img)
        except:
            pass  # If icon file doesn't exist, continue without it
        
        # Create a notebook for tabbed interface
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create main tabs
        self.main_tab = ttk.Frame(self.notebook)
        self.advanced_tab = ttk.Frame(self.notebook)
        self.about_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.main_tab, text="Main")
        self.notebook.add(self.advanced_tab, text="Advanced")
        self.notebook.add(self.about_tab, text="About")
        
        # Setup the main tab
        self.setup_main_tab()
        
        # Setup the advanced tab
        self.setup_advanced_tab()
        
        # Setup the about tab
        self.setup_about_tab()
        
        # Create output console at the bottom
        self.setup_console()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def setup_main_tab(self):
        """Set up the main tab with basic options"""
        main_frame = ttk.Frame(self.main_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Source directory selection
        source_frame = ttk.LabelFrame(main_frame, text="Source Directory", padding="10")
        source_frame.pack(fill=tk.X, pady=5)
        
        self.source_entry = ttk.Entry(source_frame, textvariable=self.source_dir, width=50)
        self.source_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        source_button = ttk.Button(source_frame, text="Browse...", command=self.browse_source)
        source_button.pack(side=tk.RIGHT, padx=5)
        
        # Destination name
        dest_frame = ttk.LabelFrame(main_frame, text="Destination Folder (on Desktop)", padding="10")
        dest_frame.pack(fill=tk.X, pady=5)
        
        self.dest_entry = ttk.Entry(dest_frame, textvariable=self.dest_name, width=50)
        self.dest_entry.pack(fill=tk.X, padx=5)
        
        # Basic options frame
        options_frame = ttk.LabelFrame(main_frame, text="Basic Options", padding="10")
        options_frame.pack(fill=tk.X, pady=5)
        
        # Checkboxes for common options
        self.move_var = tk.BooleanVar(value=False)
        move_check = ttk.Checkbutton(options_frame, text="Move files instead of copying them", 
                                     variable=self.move_var)
        move_check.grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.extract_art_var = tk.BooleanVar(value=False)
        extract_art_check = ttk.Checkbutton(options_frame, text="Extract and save album artwork", 
                                           variable=self.extract_art_var)
        extract_art_check.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        self.attach_art_var = tk.BooleanVar(value=False)
        attach_art_check = ttk.Checkbutton(options_frame, text="Attach album art to file metadata", 
                                          variable=self.attach_art_var)
        attach_art_check.grid(row=2, column=0, sticky=tk.W, pady=2)
        
        self.force_var = tk.BooleanVar(value=False)
        force_check = ttk.Checkbutton(options_frame, text="Force overwrite existing files", 
                                     variable=self.force_var)
        force_check.grid(row=3, column=0, sticky=tk.W, pady=2)
        
        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        organize_button = ttk.Button(action_frame, text="Extract & Organize Music", 
                                    command=self.run_extract_organize, width=25)
        organize_button.pack(side=tk.LEFT, padx=5)
        
        find_unknowns_button = ttk.Button(action_frame, text="Find Unknown Albums", 
                                         command=self.run_find_unknowns, width=25)
        find_unknowns_button.pack(side=tk.LEFT, padx=5)
        
        find_art_button = ttk.Button(action_frame, text="Find & Attach Album Art", 
                                    command=self.run_find_art, width=25)
        find_art_button.pack(side=tk.LEFT, padx=5)
        
    def setup_advanced_tab(self):
        """Set up the advanced tab with additional options"""
        advanced_frame = ttk.Frame(self.advanced_tab, padding="10")
        advanced_frame.pack(fill=tk.BOTH, expand=True)
        
        # Advanced options frame
        options_frame = ttk.LabelFrame(advanced_frame, text="Advanced Options", padding="10")
        options_frame.pack(fill=tk.X, pady=5)
        
        # Checkboxes for advanced options
        self.simulate_var = tk.BooleanVar(value=False)
        simulate_check = ttk.Checkbutton(options_frame, text="Simulate actions without making changes (dry run)", 
                                        variable=self.simulate_var)
        simulate_check.grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.keep_empty_var = tk.BooleanVar(value=False)
        keep_empty_check = ttk.Checkbutton(options_frame, text="Keep empty 'Unknown Album' folders", 
                                          variable=self.keep_empty_var)
        keep_empty_check.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        self.use_folders_var = tk.BooleanVar(value=True)
        use_folders_check = ttk.Checkbutton(options_frame, text="Use folder structure instead of file metadata", 
                                           variable=self.use_folders_var)
        use_folders_check.grid(row=2, column=0, sticky=tk.W, pady=2)
        
        # Additional actions frame
        action_frame = ttk.LabelFrame(advanced_frame, text="Additional Actions", padding="10")
        action_frame.pack(fill=tk.X, pady=5)
        
        clean_empty_button = ttk.Button(action_frame, text="Clean Empty 'Unknown Album' Folders", 
                                       command=self.run_clean_empty)
        clean_empty_button.pack(side=tk.LEFT, padx=5, pady=5)
        
    def setup_about_tab(self):
        """Set up the about tab with information"""
        about_frame = ttk.Frame(self.about_tab, padding="20")
        about_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(about_frame, text="I-MusicExtractor", 
                               font=("", 16, "bold"))
        title_label.pack(pady=10)
        
        # Description
        desc_text = (
            "A Python application for extracting metadata from audio files (MP3, M4A) "
            "and organizing them into folders with a hierarchical structure."
        )
        desc_label = ttk.Label(about_frame, text=desc_text, wraplength=600, justify=tk.CENTER)
        desc_label.pack(pady=10)
        
        # Features in a scrolled text widget
        features_frame = ttk.LabelFrame(about_frame, text="Features", padding="10")
        features_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        features_text = scrolledtext.ScrolledText(features_frame, wrap=tk.WORD, height=15)
        features_text.pack(fill=tk.BOTH, expand=True)
        features_text.insert(tk.END, """
• Extracts artist, title, and album metadata from MP3 and M4A files
• Creates a folder on your desktop to organize music
• Organizes audio files in a hierarchy: Artist → Album → Song
• Files without album information go into an "Unknown Album" folder
• Renames files based on their song title while preserving the original format
• Handles files with missing metadata gracefully
• Detects and skips duplicate files (same artist, album, and title)
• Option to move files instead of copying them
• Optional album artwork extraction
• Web search for missing album information
• Intelligent album identification with scoring system
• Automatic cleanup of empty "Unknown Album" folders
• Find and attach album art to files that lack it
• Multi-source album art lookup (Last.fm, Wikipedia, and DBpedia)
        """)
        features_text.config(state=tk.DISABLED)  # Make read-only
        
        # Credits
        credits_label = ttk.Label(about_frame, text="Made with ♥", justify=tk.CENTER)
        credits_label.pack(pady=10)
        
    def setup_console(self):
        """Set up the console output area"""
        console_frame = ttk.LabelFrame(self.root, text="Console Output")
        console_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.console = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, height=10)
        self.console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.console.insert(tk.END, "Welcome to I-MusicExtractor GUI!\n")
        self.console.insert(tk.END, "Ready to organize your music files.\n")
        self.console.config(state=tk.DISABLED)  # Initially read-only
        
        # Create redirector for stdout and stderr with incremental updates
        self.redirector = RedirectText(self.console, incremental=True)
        
    def browse_source(self):
        """Open file dialog to choose source directory"""
        directory = filedialog.askdirectory(title="Select Source Directory")
        if directory:
            self.source_dir.set(directory)
            
    def update_status(self, message):
        """Update status bar message"""
        self.status_var.set(message)
        self.root.update_idletasks()
        
    def enable_interface(self, enable=True):
        """Enable or disable the interface during operations"""
        state = tk.NORMAL if enable else tk.DISABLED
        
        # Disable tabs
        for tab in [self.main_tab, self.advanced_tab]:
            for child in tab.winfo_children():
                for widget in child.winfo_children():
                    if isinstance(widget, (ttk.Button, ttk.Entry, ttk.Checkbutton)):
                        widget.config(state=state)
                    elif isinstance(widget, ttk.Frame) or isinstance(widget, ttk.LabelFrame):
                        for subwidget in widget.winfo_children():
                            if isinstance(subwidget, (ttk.Button, ttk.Entry, ttk.Checkbutton)):
                                subwidget.config(state=state)
        
    def run_in_thread(self, target_function, *args, **kwargs):
        """Run a function in a separate thread with improved UI responsiveness"""
        self.console.config(state=tk.NORMAL)  # Enable console for writing
        self.console.delete(1.0, tk.END)  # Clear previous output
        
        # Disable the interface
        self.enable_interface(False)
        self.update_status("Running...")
        
        # Add a processing indicator
        self.processing_indicator = True
        self.update_processing_indicator()
        
        # Create and start the thread
        def thread_target():
            try:
                # Redirect stdout and stderr to the console
                sys.stdout = self.redirector
                sys.stderr = self.redirector
                
                # Call the target function
                result = target_function(*args, **kwargs)
                
                # Signal completion in the main thread
                self.root.after(100, lambda: self.handle_thread_completion("Completed"))
                return result
            except Exception as e:
                # Show error in the console
                print(f"\nError: {e}")
                # Signal error in the main thread
                self.root.after(100, lambda: self.handle_thread_completion("Error occurred"))
            finally:
                # Reset stdout and stderr
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__
        
        threading.Thread(target=thread_target, daemon=True).start()
    
    def update_processing_indicator(self):
        """Update the processing indicator in the status bar"""
        if hasattr(self, 'processing_indicator') and self.processing_indicator:
            # Rotate through different indicator states
            current_status = self.status_var.get()
            if current_status.endswith("..."):
                self.status_var.set("Running.")
            elif current_status.endswith(".."):
                self.status_var.set("Running...")
            elif current_status.endswith("."):
                self.status_var.set("Running..")
            else:
                self.status_var.set("Running.")
            
            # Schedule the next update
            self.root.after(300, self.update_processing_indicator)
    
    def handle_thread_completion(self, status_message):
        """Handle thread completion and update UI accordingly"""
        # Stop the processing indicator
        self.processing_indicator = False
        
        # Re-enable the interface
        self.enable_interface(True)
        
        # Update status
        self.update_status(status_message)
        
        # Make sure the console shows the latest output
        self.redirector.flush()
        
    def run_extract_organize(self):
        """Run the main extract and organize operation"""
        # Create a custom implementation that directly uses the functions we need
        def run_main():
            try:
                source_dir = Path(self.source_dir.get())
                if not source_dir.exists() or not source_dir.is_dir():
                    print(f"Error: Source directory '{source_dir}' does not exist or is not a directory.")
                    return
                
                print(f"Using source directory: {source_dir}")
                
                # Prepare destination directory
                desktop_path = Path.home() / "Desktop"
                dest_dir = desktop_path / self.dest_name.get()
                
                # Create destination directory if it doesn't exist
                if not dest_dir.exists():
                    os.makedirs(dest_dir)
                    print(f"Created directory: {dest_dir}")
                
                # Process files
                move_files = self.move_var.get()
                extract_art = self.extract_art_var.get()
                force = self.force_var.get()
                attach_art = self.attach_art_var.get()
                use_folders = self.use_folders_var.get()
                simulate = self.simulate_var.get()
                keep_empty = self.keep_empty_var.get()
                
                # Track statistics
                total_files = 0
                duplicate_count = 0
                duplicates_list = []
                processed_files = []  # Track processed files
                art_cache = {}  # Cache for album art
                
                print(f"\nProcessing files from {source_dir} to {dest_dir}")
                print(f"Options: Move={move_files}, ExtractArt={extract_art}, Force={force}, AttachArt={attach_art}")
                
                # Process each file - this is a simplified version of the main processing loop
                supported_extensions = ['.mp3', '.m4a']
                
                for file in source_dir.glob("*.*"):
                    if file.suffix.lower() not in supported_extensions:
                        print(f"Skipping unsupported file: {file}")
                        continue
                        
                    try:
                        total_files += 1
                        print(f"\nProcessing file: {file}")
                        
                        # Extract metadata using the function from the main script
                        metadata = music_extractor.extract_metadata(file)
                        
                        # Continue with the rest of the processing
                        artist_name = music_extractor.sanitize_filename(metadata['artist'])
                        album_name = music_extractor.sanitize_filename(metadata['album'])
                        title_name = music_extractor.sanitize_filename(metadata['title'])
                        
                        # Check for duplicates
                        file_signature = f"{artist_name}|{album_name}|{title_name}"
                        if file_signature in processed_files:
                            duplicate_count += 1
                            duplicates_list.append(f"{artist_name} - {album_name} - {title_name} ({file.name})")
                            print(f"DUPLICATE FOUND: {artist_name} - {album_name} - {title_name}")
                            print(f"Skipping duplicate file: {file}")
                            if not force:
                                continue
                        
                        processed_files.append(file_signature)
                        
                        # Create artist directory
                        artist_dir = dest_dir / artist_name
                        if not artist_dir.exists():
                            os.makedirs(artist_dir)
                            print(f"Created artist directory: {artist_dir}")
                        
                        # Check for existing file in another folder
                        song_already_exists = False
                        if album_name == "Unknown Album":
                            for album_folder in artist_dir.iterdir():
                                if album_folder.is_dir() and album_folder.name != "Unknown Album":
                                    potential_file = album_folder / f"{title_name}{file.suffix}"
                                    if potential_file.exists():
                                        print(f"File already exists in a known album: {potential_file}")
                                        print(f"Skipping to avoid duplicating in Unknown Album folder")
                                        song_already_exists = True
                                        break
                                        
                            if song_already_exists and not force:
                                continue
                        
                        # Create album directory
                        album_dir = artist_dir / album_name
                        if not album_dir.exists():
                            os.makedirs(album_dir)
                            print(f"Created album directory: {album_dir}")
                        
                        # Extract album art if requested
                        if extract_art:
                            music_extractor.extract_and_save_album_art(file, album_dir)
                        
                        # Create destination path
                        new_filename = f"{title_name}{file.suffix}"
                        dest_path = album_dir / new_filename
                        
                        # Check if file already exists
                        if dest_path.exists() and not force:
                            print(f"File already exists at destination: {dest_path}")
                            print("Skipping to avoid overwriting. Use force option to override.")
                            continue
                        
                        # Copy or move the file
                        if not simulate:
                            if move_files:
                                shutil.move(file, dest_path)
                                print(f"Moved '{file.name}' to '{dest_path}'")
                            else:
                                shutil.copy2(file, dest_path)
                                print(f"Copied '{file.name}' to '{dest_path}'")
                        else:
                            print(f"[SIMULATE] Would {'move' if move_files else 'copy'} '{file.name}' to '{dest_path}'")
                        
                        # Attach album art if requested
                        if attach_art and not simulate:
                            try:
                                if not music_extractor.has_album_art(dest_path):
                                    print(f"File doesn't have album art, attempting to find and attach: {dest_path}")
                                    
                                    # Create a cache key
                                    cache_key = f"{metadata['artist']}|{metadata['album']}"
                                    
                                    # Check for cached art
                                    image_data = None
                                    if cache_key in self.art_cache:
                                        print(f"Using cached album art for {metadata['artist']} - {metadata['album']}")
                                        image_data = self.art_cache[cache_key]
                                    else:
                                        # Search for album art online
                                        image_data = music_extractor.search_album_art_online(
                                            metadata['artist'], 
                                            metadata['album'], 
                                            metadata['title']
                                        )
                                        
                                        if image_data:
                                            self.art_cache[cache_key] = image_data
                                            print(f"Found and cached album art for {metadata['artist']} - {metadata['album']}")
                                    
                                    # Attach the art if found
                                    if image_data:
                                        if music_extractor.attach_album_art(dest_path, image_data):
                                            print(f"Successfully attached album art to file: {dest_path}")
                                        else:
                                            print(f"Failed to attach album art to file: {dest_path}")
                            except Exception as e:
                                print(f"Error during album art attachment: {e}")
                    
                    except Exception as e:
                        print(f"Error processing {file}: {e}")
                
                # Print summary of duplicates
                if duplicate_count > 0:
                    print("\n" + "="*50)
                    print(f"Found {duplicate_count} duplicate files:")
                    for duplicate in duplicates_list:
                        print(f"  - {duplicate}")
                    print("These files were skipped. Use Force option to override.")
                    print("="*50)
                
                # Clean up empty folders
                if not keep_empty and not simulate:
                    removed = music_extractor.clean_empty_unknown_album_folders(dest_dir, False)
                    if removed > 0:
                        print(f"Removed {removed} empty 'Unknown Album' folders")
                
                print("\nMusic extraction and organization complete!")
                print(f"Processed {total_files} files.")
            
            except Exception as e:
                print(f"Error during processing: {e}")
        
        # Run the custom implementation in a thread
        self.run_in_thread(run_main)
        
    def run_find_unknowns(self):
        """Run the find unknowns operation"""
        def run_find_unknowns_task():
            try:
                desktop_path = Path.home() / "Desktop"
                dest_dir = desktop_path / self.dest_name.get()
                
                if not dest_dir.exists():
                    print(f"Error: Destination directory {dest_dir} does not exist.")
                    return
                
                print(f"Finding unknown albums in {dest_dir}")
                
                # Get GUI options
                extract_art = self.extract_art_var.get()
                simulate = self.simulate_var.get()
                keep_empty = self.keep_empty_var.get()
                
                # Create optimized version that uses the GUI's caches
                def find_unknown_albums_optimized(base_dir, extract_art, simulate, clean_empty):
                    # Track statistics
                    total_unknown_files = 0
                    files_with_found_albums = 0
                    
                    # Use the GUI's cache
                    album_cache = self.album_info_cache
                    
                    # First, scan to collect all unknown album files
                    unknown_files = []
                    unknown_albums_dirs = []
                    songs_to_lookup = set()
                    
                    for artist_dir in base_dir.iterdir():
                        if not artist_dir.is_dir():
                            continue
                            
                        unknown_album_dir = artist_dir / "Unknown Album"
                        if not unknown_album_dir.exists() or not unknown_album_dir.is_dir():
                            continue
                            
                        unknown_albums_dirs.append(unknown_album_dir)
                        
                        for file in unknown_album_dir.glob("*.*"):
                            if file.suffix.lower() not in ['.mp3', '.m4a']:
                                continue
                                
                            total_unknown_files += 1
                            
                            # Extract metadata
                            metadata = music_extractor.extract_metadata(file)
                            artist = metadata['artist']
                            title = metadata['title']
                            
                            # Add to processing list
                            unknown_files.append((file, artist, title, artist_dir))
                            
                            # Add to lookup set for batch processing
                            songs_to_lookup.add((artist, title))
                    
                    if not unknown_files:
                        print("No files found in Unknown Album folders")
                        return 0
                    
                    print(f"Found {total_unknown_files} files in Unknown Album folders")
                    
                    # Prefetch album information in batch
                    if songs_to_lookup and not simulate:
                        print(f"Prefetching album information for {len(songs_to_lookup)} unique artist/title combinations...")
                        
                        for artist, title in songs_to_lookup:
                            cache_key = f"{artist}|{title}"
                            if cache_key not in album_cache:
                                # Try to find album info
                                print(f"Searching for album: {artist} - {title}")
                                album = music_extractor.search_album_info(artist, title)
                                if album:
                                    album_cache[cache_key] = album
                                    print(f"Found album: {album} for {artist} - {title}")
                                else:
                                    # Store None to avoid repeated lookups
                                    album_cache[cache_key] = None
                                    print(f"No album found for {artist} - {title}")
                    
                    # Process files with prefetched album info
                    for file, artist, title, artist_dir in unknown_files:
                        print(f"\nProcessing file: {file}")
                        
                        # Check cache for album info
                        cache_key = f"{artist}|{title}"
                        album = album_cache.get(cache_key)
                        
                        if simulate:
                            if album and album != "Unknown Album":
                                files_with_found_albums += 1
                                print(f"[SIMULATE] Would move {file.name} to album: {album}")
                            continue
                        
                        # If we have album info, reorganize the file
                        if album and album != "Unknown Album":
                            files_with_found_albums += 1
                            
                            # Sanitize album name
                            album_name = music_extractor.sanitize_filename(album)
                            
                            # Create the destination album directory
                            album_dir = artist_dir / album_name
                            if not album_dir.exists():
                                os.makedirs(album_dir)
                                print(f"Created album directory: {album_dir}")
                                
                            # Extract album art if requested
                            if extract_art:
                                music_extractor.extract_and_save_album_art(file, album_dir)
                            
                            # Move the file to the new album directory
                            dest_path = album_dir / file.name
                            try:
                                shutil.move(file, dest_path)
                                print(f"Moved '{file.name}' to '{dest_path}'")
                            except Exception as e:
                                print(f"Error moving file: {e}")
                    
                    # Clean up empty Unknown Album folders if requested
                    removed_folders = 0
                    if clean_empty:
                        print("\nCleaning up empty 'Unknown Album' folders...")
                        removed_folders = music_extractor.clean_empty_unknown_album_folders(base_dir, simulate)
                    
                    # Print summary
                    print("\n" + "="*50)
                    print(f"Found {total_unknown_files} files in Unknown Album folders")
                    print(f"Successfully found album information for {files_with_found_albums} files")
                    print(f"Moved {files_with_found_albums} files to their proper album folders")
                    if clean_empty:
                        print(f"Removed {removed_folders} empty 'Unknown Album' folders")
                    print("="*50)
                    
                    return files_with_found_albums
                
                # Call our optimized function
                files_moved = find_unknown_albums_optimized(
                    dest_dir, 
                    extract_art,
                    simulate,
                    not keep_empty  # clean_empty parameter is the opposite of keep_empty
                )
                
                print(f"\nFound and processed {files_moved} files from 'Unknown Album' folders.")
                
                # Additional cleanup is handled inside our optimized function
                if not keep_empty and not simulate:
                    print("\nEmpty 'Unknown Album' folders were cleaned up during processing.")
                        
                print("\nFind unknown albums operation complete!")
                
            except Exception as e:
                print(f"Error during find unknowns operation: {e}")
        
        # Run the task in a thread
        self.run_in_thread(run_find_unknowns_task)
        
    def run_find_art(self):
        """Run the find and attach album art operation"""
        def run_find_art_task():
            try:
                desktop_path = Path.home() / "Desktop"
                dest_dir = desktop_path / self.dest_name.get()
                
                if not dest_dir.exists():
                    print(f"Error: Destination directory {dest_dir} does not exist.")
                    return
                
                print(f"Finding and attaching album art for files in {dest_dir}")
                
                # Get GUI options
                simulate = self.simulate_var.get()
                use_folders = self.use_folders_var.get()
                keep_empty = self.keep_empty_var.get()
                
                # Modify the find_and_attach_album_art function to use our cache
                def find_and_attach_with_cache(dest_dir, simulate, use_folders):
                    # Create local copy of the cache reference
                    art_cache = self.art_cache
                    
                    # Metrics
                    total_files = 0
                    files_without_art = 0
                    files_updated = 0
                    files_failed = 0
                    files_moved = 0
                    
                    print(f"\nScanning for files without album art in {dest_dir}")
                    
                    # First scan to collect all files needing art
                    files_to_process = []
                    albums_to_check = set()
                    
                    for root, dirs, files in os.walk(dest_dir):
                        root_path = Path(root)
                        if root_path == dest_dir:
                            continue
                            
                        for file in files:
                            file_path = root_path / file
                            file_ext = file_path.suffix.lower()
                            
                            if file_ext not in ['.mp3', '.m4a']:
                                continue
                                
                            total_files += 1
                            
                            # Check if file has art
                            if not music_extractor.has_album_art(file_path):
                                files_without_art += 1
                                
                                # Extract metadata
                                if use_folders:
                                    parts = file_path.parts
                                    if len(parts) >= 3:
                                        album = parts[-2]
                                        artist = parts[-3]
                                        if artist == dest_dir.name:
                                            artist = album
                                            album = "Unknown Album"
                                        title = file_path.stem
                                    else:
                                        metadata = music_extractor.extract_metadata(file_path)
                                        artist = metadata['artist']
                                        album = metadata['album']
                                        title = metadata['title']
                                else:
                                    metadata = music_extractor.extract_metadata(file_path)
                                    artist = metadata['artist']
                                    album = metadata['album']
                                    title = metadata['title']
                                
                                # Add to processing list
                                files_to_process.append((file_path, artist, album, title))
                                
                                # Add to albums to prefetch
                                albums_to_check.add((artist, album))
                    
                    print(f"Found {files_without_art} files without album art out of {total_files} total files")
                    
                    # Prefetch album art in batch to reduce redundant network requests
                    if albums_to_check and not simulate:
                        print(f"Prefetching album art for {len(albums_to_check)} unique artist/album combinations...")
                        
                        for artist, album in albums_to_check:
                            cache_key = f"{artist}|{album}"
                            if cache_key not in art_cache:
                                # Try to find art once
                                print(f"Searching for art: {artist} - {album}")
                                image_data = music_extractor.search_album_art_online(artist, album, "")
                                if image_data:
                                    art_cache[cache_key] = image_data
                                    print(f"Found and cached art for {artist} - {album}")
                                else:
                                    # Store None to avoid repeated lookups
                                    art_cache[cache_key] = None
                                    print(f"No art found for {artist} - {album}")
                    
                    # Now process each file with the prefetched art
                    for file_path, artist, album, title in files_to_process:
                        print(f"Processing: {file_path}")
                        
                        is_in_unknown_album = "Unknown Album" in str(file_path)
                        
                        # Check cached art
                        cache_key = f"{artist}|{album}"
                        image_data = art_cache.get(cache_key)
                        
                        if simulate:
                            print(f"[SIMULATE] Would attach art to {file_path}")
                            files_updated += 1
                            continue
                        
                        # Attach art if available
                        if image_data:
                            if music_extractor.attach_album_art(file_path, image_data):
                                files_updated += 1
                                print(f"Successfully attached art to {file_path}")
                                
                                # Handle Unknown Album case
                                if is_in_unknown_album:
                                    try:
                                        # See if we can get real album info
                                        artist_title_key = f"{artist}|{title}"
                                        
                                        if artist_title_key in self.album_info_cache:
                                            real_album = self.album_info_cache[artist_title_key]
                                        else:
                                            real_album = music_extractor.search_album_info(artist, title)
                                            self.album_info_cache[artist_title_key] = real_album
                                        
                                        if real_album and real_album != "Unknown Album":
                                            # Get artist directory
                                            artist_dir = file_path.parent.parent
                                            
                                            # Create album directory
                                            album_name = music_extractor.sanitize_filename(real_album)
                                            album_dir = artist_dir / album_name
                                            if not album_dir.exists():
                                                os.makedirs(album_dir)
                                            
                                            # Move the file
                                            dest_path = album_dir / file_path.name
                                            if not dest_path.exists():
                                                shutil.move(file_path, dest_path)
                                                print(f"Moved file to {album_name}: {dest_path}")
                                                files_moved += 1
                                    except Exception as e:
                                        print(f"Error moving file: {e}")
                            else:
                                files_failed += 1
                                print(f"Failed to attach art to {file_path}")
                        else:
                            print(f"No art available for {file_path}")
                    
                    # Clean up empty folders if needed
                    removed = 0
                    if not keep_empty and files_moved > 0:
                        removed = music_extractor.clean_empty_unknown_album_folders(dest_dir, False)
                    
                    # Return stats
                    return files_updated, files_moved, removed
                
                # Call our modified function instead
                files_updated, files_moved, removed = find_and_attach_with_cache(dest_dir, simulate, use_folders)
                
                print(f"\nUpdated {files_updated} files with album art.")
                if files_moved > 0:
                    print(f"Moved {files_moved} files to more appropriate album folders.")
                
                # Clean up empty Unknown Album folders if not keeping empty folders
                if removed > 0:
                    print(f"Removed {removed} empty 'Unknown Album' folders")
                        
                print("\nFind and attach album art operation complete!")
                
            except Exception as e:
                print(f"Error during find and attach album art operation: {e}")
        
        # Run the task in a thread
        self.run_in_thread(run_find_art_task)
        
    def run_clean_empty(self):
        """Run the clean empty Unknown Album folders operation"""
        # Get the destination directory
        desktop_path = Path.home() / "Desktop"
        dest_dir = desktop_path / self.dest_name.get()
        
        if not dest_dir.exists():
            print(f"Error: Destination directory {dest_dir} does not exist.")
            return
        
        # Run in a separate thread
        def run_clean():
            print(f"Cleaning empty 'Unknown Album' folders in {dest_dir}")
            removed = music_extractor.clean_empty_unknown_album_folders(dest_dir, self.simulate_var.get())
            print(f"Removed {removed} empty 'Unknown Album' folders")
        
        self.run_in_thread(run_clean)

def main():
    # Create and run the GUI
    root = tk.Tk()
    app = MusicExtractorGUI(root)
    
    # Apply platform-specific settings
    if os.name == 'nt':  # Windows
        # Use Windows-style theme
        style = ttk.Style()
        style.theme_use('vista')
    
    # Center the window on screen
    window_width = 900
    window_height = 700
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # Start the main loop
    root.mainloop()

if __name__ == "__main__":
    main() 