#!/usr/bin/env python3
"""
Script to convert a PNG image to an ICO file for Windows applications
"""

import os
from pathlib import Path
from PIL import Image

def create_windows_icon(png_path="music_icon.png", ico_path="music_icon.ico"):
    """
    Convert a PNG image to an ICO file with multiple sizes
    for Windows applications
    
    Args:
        png_path: Path to the source PNG file
        ico_path: Path to the output ICO file
    """
    print(f"Creating Windows icon...")
    
    # Check if source file exists
    if not os.path.exists(png_path):
        print(f"Error: Source file '{png_path}' not found.")
        return False
    
    try:
        # Open the PNG image
        img = Image.open(png_path)
        
        # Define icon sizes for Windows
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        
        # Create resized versions
        img_list = []
        for size in icon_sizes:
            resized_img = img.resize(size, Image.Resampling.LANCZOS)
            img_list.append(resized_img)
        
        # Save as ICO file
        img_list[0].save(
            ico_path, 
            format='ICO', 
            sizes=[(img.width, img.height) for img in img_list],
            append_images=img_list[1:]
        )
        
        print(f"Successfully created {ico_path}")
        return True
    
    except Exception as e:
        print(f"Error creating Windows icon: {e}")
        return False

if __name__ == "__main__":
    create_windows_icon() 