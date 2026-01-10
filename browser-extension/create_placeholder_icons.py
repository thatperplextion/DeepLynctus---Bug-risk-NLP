# Simple icon placeholder generator
# Creates minimal PNG icons without external dependencies

from pathlib import Path
import base64

# Minimal 1x1 pixel PNGs in base64 (will be replaced with real icons)
# These are valid PNG files that browsers can render

# 16x16 simple gradient icon
icon_16 = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAD3SURBVDiNpZK9SgNBFIW/2V0TjBqwMoWFhYWFpYWNhY2VhY2VhYWFhYWFhYWVhYWFhYWNhYWNhYWFhYWNhYWFhYWNhYWFhYWFhYWFhYWNhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhQ=='
)

# Create icons directory
icons_dir = Path('icons')
icons_dir.mkdir(exist_ok=True)

# For now, create simple colored square placeholders
# You'll need to replace these with proper icons before publishing

print("Creating placeholder icons...")
print("⚠️  These are basic placeholders - replace with proper icons before publishing!\n")

# Create a simple colored square for each size using PIL
try:
    from PIL import Image, ImageDraw, ImageFont
    
    def create_icon(size, filename):
        # Create gradient background
        img = Image.new('RGB', (size, size))
        draw = ImageDraw.Draw(img)
        
        # Draw gradient-like squares
        for i in range(size):
            ratio = i / size
            r = int(6 + ratio * (139 - 6))
            g = int(182 + ratio * (92 - 182))
            b = int(212 + ratio * (246 - 212))
            draw.line([(0, i), (size, i)], fill=(r, g, b))
        
        # Draw brain emoji text if size allows
        if size >= 48:
            try:
                font = ImageFont.truetype("seguiemj.ttf", size // 2)
                draw.text((size // 4, size // 4), "🧠", font=font, embedded_color=True)
            except:
                # Fallback to simple circle
                draw.ellipse([size//4, size//4, 3*size//4, 3*size//4], fill='white')
        else:
            # Small sizes - just a circle
            draw.ellipse([size//4, size//4, 3*size//4, 3*size//4], fill='white')
        
        # Save
        img.save(icons_dir / filename)
        print(f"✅ Created {filename} ({size}x{size})")
    
    create_icon(16, 'icon16.png')
    create_icon(48, 'icon48.png')
    create_icon(128, 'icon128.png')
    
    print("\n✨ Placeholder icons created!")
    print("\n📝 Next steps:")
    print("   1. Open icons/icon.svg in a graphics editor")
    print("   2. Export as PNG at 16x16, 48x48, 128x128")
    print("   3. Replace the placeholder files")
    print("\n   Or use online tool: https://svgtopng.com/")

except ImportError:
    print("⚠️  PIL not available - creating minimal placeholders")
    
    # Create absolute minimal valid PNG files
    # This is a 1x1 transparent PNG that will work but look bad
    minimal_png = base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
    )
    
    for filename in ['icon16.png', 'icon48.png', 'icon128.png']:
        with open(icons_dir / filename, 'wb') as f:
            f.write(minimal_png)
        print(f"⚠️  Created minimal {filename} (replace me!)")
    
    print("\n❌ Install Pillow for better placeholders:")
    print("   pip install Pillow")
    print("\n   Or create proper icons manually/online")

print(f"\n📁 Icons saved to: {icons_dir.absolute()}")
