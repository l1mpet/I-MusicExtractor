#!/usr/bin/env python3
import os
from PIL import Image, ImageDraw, ImageFont

def create_music_icon(size=256, color="#4285F4", background="#FFFFFF"):
    """Create a simple music note icon"""
    # Create a new blank image with white background
    img = Image.new("RGBA", (size, size), background)
    draw = ImageDraw.Draw(img)
    
    # Draw a music note (simplified)
    # Draw the note head (oval)
    head_width = size * 0.3
    head_height = size * 0.24
    head_x = size * 0.35
    head_y = size * 0.5
    draw.ellipse(
        [(head_x, head_y), (head_x + head_width, head_y + head_height)],
        fill=color
    )
    
    # Draw the stem
    stem_width = size * 0.08
    stem_x = head_x + head_width - stem_width/2
    stem_y1 = head_y  # Start at the top of the note head
    stem_y2 = size * 0.25  # End at the top of the stem (smaller value)
    
    # Make sure y2 < y1 for the rectangle
    if stem_y1 > stem_y2:
        draw.rectangle(
            [(stem_x, stem_y2), (stem_x + stem_width, stem_y1)],
            fill=color
        )
    else:
        draw.rectangle(
            [(stem_x, stem_y1), (stem_x + stem_width, stem_y2)],
            fill=color
        )
    
    # Draw the flag
    flag_width = size * 0.25
    flag_height = size * 0.15
    flag_x1 = stem_x + stem_width
    flag_y1 = stem_y2
    flag_x2 = flag_x1 + flag_width
    flag_y2 = flag_y1 + flag_height
    
    # Draw a curved flag (using a bezier curve approximation with polygon)
    points = [
        (flag_x1, flag_y1),
        (flag_x1 + flag_width * 0.8, flag_y1 + flag_height * 0.2),
        (flag_x1 + flag_width * 0.9, flag_y1 + flag_height * 0.5),
        (flag_x1 + flag_width * 0.8, flag_y1 + flag_height * 0.8),
        (flag_x1, flag_y1 + flag_height)
    ]
    draw.polygon(points, fill=color)
    
    return img

def main():
    """Create music icon files for the application"""
    # Create icons directory if it doesn't exist
    if not os.path.exists("icons"):
        os.makedirs("icons")
    
    # Generate PNG icons in different sizes
    sizes = [16, 32, 48, 64, 128, 256]
    icons = []
    
    for size in sizes:
        icon = create_music_icon(size=size)
        icon_path = f"icons/music_icon_{size}.png"
        icon.save(icon_path)
        print(f"Created {icon_path}")
        icons.append(icon)
    
    # Save the 256px version as the main icon
    icons[-1].save("music_icon.png")
    print("Created music_icon.png")
    
    # Create Windows ICO file (requires all sizes)
    # The first icon in the list is used as the default
    try:
        icons[0].save("music_icon.ico", 
                      format="ICO", 
                      sizes=[(s, s) for s in sizes])
        print("Created music_icon.ico")
    except Exception as e:
        print(f"Could not create ICO file: {e}")
        print("Windows ICO file creation may only work on Windows.")
    
    print("Icon generation complete!")

if __name__ == "__main__":
    main() 