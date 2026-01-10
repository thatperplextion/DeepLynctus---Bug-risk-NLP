# Convert SVG icon to PNG files at different sizes
# Requires: pip install cairosvg pillow

try:
    from cairosvg import svg2png
    from PIL import Image
    from io import BytesIO
    from pathlib import Path
    
    icons_dir = Path('icons')
    icons_dir.mkdir(exist_ok=True)
    
    # Read SVG
    with open(icons_dir / 'icon.svg', 'r', encoding='utf-8') as f:
        svg_data = f.read()
    
    # Generate PNG files at different sizes
    sizes = {
        'icon16.png': 16,
        'icon48.png': 48,
        'icon128.png': 128
    }
    
    for filename, size in sizes.items():
        # Convert SVG to PNG
        png_data = svg2png(bytestring=svg_data.encode('utf-8'), output_width=size, output_height=size)
        
        # Save file
        output_path = icons_dir / filename
        with open(output_path, 'wb') as f:
            f.write(png_data)
        
        print(f"✅ Created {filename} ({size}x{size})")
    
    print("\n🎉 All icons generated successfully!")
    print(f"\nGenerated files in {icons_dir.absolute()}:")
    for file in icons_dir.glob('*.png'):
        print(f"  - {file.name}")

except ImportError as e:
    print("❌ Required packages not installed")
    print("\nInstall with:")
    print("  pip install cairosvg pillow")
    print("\nOr use online converter:")
    print("  1. Upload icons/icon.svg to https://svgtopng.com/")
    print("  2. Generate 16x16, 48x48, and 128x128 versions")
    print("  3. Save as icon16.png, icon48.png, icon128.png in icons/ folder")
    
except FileNotFoundError:
    print("❌ icon.svg not found")
    print("Run generate_icons.py first to create the SVG file")

except Exception as e:
    print(f"❌ Error: {e}")
    print("\nAs a fallback, you can:")
    print("  1. Open icons/icon.svg in a browser")
    print("  2. Take screenshots at different zoom levels")
    print("  3. Crop and resize to 16x16, 48x48, 128x128")
    print("  4. Save as PNG files in icons/ folder")
