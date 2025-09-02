#!/usr/bin/env python3
"""
Zodiac Sprite Slicer for SoulBridge AI
Slices zodiac sprite sheets into individual sign images for horoscope feature

Usage:
    python slice_zodiac_sprite.py <sprite_sheet.png> [--output-dir output/]
    
Features:
- Auto-detects grid layout (3x4, 4x3, 6x2, etc.)
- Names files with zodiac sign names (aries.png, taurus.png, etc.)
- Supports PNG, JPG, WEBP input formats
- Configurable output directory
- Maintains aspect ratio and quality
"""

import os
import sys
import argparse
from PIL import Image
from pathlib import Path

# Zodiac signs in standard order
ZODIAC_SIGNS = [
    'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
    'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'
]

# Common sprite sheet layouts (cols, rows)
COMMON_LAYOUTS = [
    (6, 2),  # 6 columns, 2 rows
    (4, 3),  # 4 columns, 3 rows  
    (3, 4),  # 3 columns, 4 rows
    (2, 6),  # 2 columns, 6 rows
    (12, 1), # 12 columns, 1 row
    (1, 12)  # 1 column, 12 rows
]

def detect_layout(width, height, total_signs=12):
    """Auto-detect the most likely grid layout"""
    best_layout = None
    best_score = float('inf')
    
    for cols, rows in COMMON_LAYOUTS:
        if cols * rows >= total_signs:
            tile_width = width / cols
            tile_height = height / rows
            
            # Prefer square-ish tiles
            aspect_ratio = max(tile_width, tile_height) / min(tile_width, tile_height)
            score = aspect_ratio + (cols * rows - total_signs) * 0.1  # Penalty for extra slots
            
            if score < best_score:
                best_score = score
                best_layout = (cols, rows, tile_width, tile_height)
    
    return best_layout

def slice_sprite_sheet(sprite_path, output_dir, layout=None):
    """Slice sprite sheet into individual zodiac sign images"""
    
    # Load sprite sheet
    try:
        sprite = Image.open(sprite_path)
        print(f"📷 Loaded sprite sheet: {sprite.size[0]}x{sprite.size[1]} pixels")
    except Exception as e:
        print(f"❌ Error loading sprite sheet: {e}")
        return False
    
    width, height = sprite.size
    
    # Auto-detect layout if not provided
    if not layout:
        layout = detect_layout(width, height)
        if not layout:
            print("❌ Could not detect sprite sheet layout")
            return False
        
        cols, rows, tile_width, tile_height = layout
        print(f"🔍 Detected layout: {cols}x{rows} grid ({int(tile_width)}x{int(tile_height)} per tile)")
    else:
        cols, rows = layout
        tile_width = width / cols
        tile_height = height / rows
        print(f"📐 Using specified layout: {cols}x{rows} grid ({int(tile_width)}x{int(tile_height)} per tile)")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Slice and save individual signs
    saved_count = 0
    for i in range(min(12, cols * rows)):
        # Calculate position in grid
        col = i % cols
        row = i // cols
        
        # Calculate crop boundaries
        left = int(col * tile_width)
        top = int(row * tile_height)
        right = int((col + 1) * tile_width)
        bottom = int((row + 1) * tile_height)
        
        # Crop tile
        tile = sprite.crop((left, top, right, bottom))
        
        # Save with zodiac sign name
        sign_name = ZODIAC_SIGNS[i]
        output_path = os.path.join(output_dir, f"{sign_name}.png")
        
        try:
            tile.save(output_path, 'PNG', optimize=True)
            print(f"✅ Saved: {sign_name}.png ({tile.size[0]}x{tile.size[1]})")
            saved_count += 1
        except Exception as e:
            print(f"❌ Error saving {sign_name}.png: {e}")
    
    print(f"\n🎉 Successfully sliced {saved_count}/12 zodiac signs!")
    return True

def main():
    parser = argparse.ArgumentParser(description='Slice zodiac sprite sheets into individual sign images')
    parser.add_argument('sprite_sheet', help='Path to the zodiac sprite sheet image')
    parser.add_argument('--output-dir', '-o', default='zodiac_signs/', help='Output directory for individual sign images')
    parser.add_argument('--layout', help='Manual layout as "COLSxROWS" (e.g., "4x3")')
    parser.add_argument('--list-layouts', action='store_true', help='List common sprite sheet layouts')
    
    args = parser.parse_args()
    
    if args.list_layouts:
        print("Common zodiac sprite sheet layouts:")
        for cols, rows in COMMON_LAYOUTS:
            print(f"  {cols}x{rows} ({cols * rows} total slots)")
        return
    
    # Validate input file
    if not os.path.exists(args.sprite_sheet):
        print(f"❌ Sprite sheet not found: {args.sprite_sheet}")
        return
    
    # Parse manual layout if provided
    layout = None
    if args.layout:
        try:
            cols, rows = map(int, args.layout.split('x'))
            layout = (cols, rows)
            print(f"📐 Using manual layout: {cols}x{rows}")
        except ValueError:
            print("❌ Invalid layout format. Use COLSxROWS (e.g., '4x3')")
            return
    
    # Slice the sprite sheet
    success = slice_sprite_sheet(args.sprite_sheet, args.output_dir, layout)
    
    if success:
        print(f"\n📁 Output directory: {os.path.abspath(args.output_dir)}")
        print("🔮 Individual zodiac sign images ready for horoscope feature!")
    else:
        print("\n💥 Sprite slicing failed!")

if __name__ == '__main__':
    main()