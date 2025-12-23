#!/usr/bin/env python3
"""
Setup script to create BioAuthAI favicon for frontend only.
Backend should NOT have a static folder - it's API only!

Usage: python setup_favicon.py
"""

import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow is required.")
    print("Install with: pip install Pillow")
    sys.exit(1)

def create_bioauthai_favicon():
    """Create a professional BioAuthAI favicon."""

    # Create a 64x64 image with transparency
    size = 64
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle (blue)
    draw.ellipse([2, 2, 62, 62], fill='#3B82F6', outline='#1E40AF', width=2)

    # Keyboard keys (white squares representing keystroke biometrics)
    key_color = '#FFFFFF'

    # Top-left key
    draw.rounded_rectangle([16, 18, 26, 28], radius=2, fill=key_color, outline=None)

    # Top-right key
    draw.rounded_rectangle([30, 18, 40, 28], radius=2, fill=key_color, outline=None)

    # Bottom-left key
    draw.rounded_rectangle([16, 32, 26, 42], radius=2, fill=key_color, outline=None)

    # Bottom-right key
    draw.rounded_rectangle([30, 32, 40, 42], radius=2, fill=key_color, outline=None)

    # Security shield (green accent)
    shield_points = [(48, 26), (52, 24), (56, 26), (56, 34), (52, 38), (48, 34)]
    draw.polygon(shield_points, fill='#10B981', outline='#059669')

    # Add "BA" text
    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except:
        font = ImageFont.load_default()

    text = "BA"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (size - text_width) // 2
    text_y = 48

    draw.text((text_x, text_y), text, fill='#FFFFFF', font=font)

    # Frontend public folder
    frontend_public = os.path.join("..", "frontend", "public")

    # Create multiple sizes
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
    images = [img.resize(s, Image.Resampling.LANCZOS) for s in sizes]

    # Save favicon.ico
    ico_path = os.path.join(frontend_public, "favicon.ico")
    images[0].save(
        ico_path,
        format='ICO',
        sizes=sizes,
        append_images=images[1:]
    )

    # Save PNG logo
    png_path = os.path.join(frontend_public, "bioauthai-logo.png")
    img.save(png_path, format='PNG')

    print("[SUCCESS] BioAuthAI favicon created!")
    print(f"   Frontend favicon: {ico_path}")
    print(f"   Frontend logo: {png_path}")
    print(f"   Sizes: {', '.join([f'{s[0]}x{s[1]}' for s in sizes])}")
    print("\nBackend does NOT have a static folder - it's API only!")

if __name__ == "__main__":
    try:
        create_bioauthai_favicon()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
