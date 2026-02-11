"""
gymratHD Logo Creator v1.0
===========================

Creates beautiful crown logos with zero errors.
Simple, reliable, works every time.

Created by: github.com/barebonesjones
"""

def create_crown_logo():
    """Create beautiful crown logo - bulletproof version"""
    try:
        from PIL import Image, ImageDraw
        print("🎨 Creating gymratHD crown logo...")
        
        # Logo settings
        size = (128, 128)
        crown_gold = '#FFD700'
        electric_blue = '#0047FF'
        energy_red = '#FF0000'
        deep_black = '#000000'
        
        # Create transparent image
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Crown base
        base_points = [(20, 85), (108, 85), (110, 105), (18, 105)]
        draw.polygon(base_points, fill=crown_gold, outline=electric_blue, width=2)
        
        # Crown peaks
        # Left peak
        left_peak = [(20, 85), (35, 85), (27, 45)]
        draw.polygon(left_peak, fill=crown_gold, outline=electric_blue, width=2)
        
        # Center peak (tallest)
        center_peak = [(45, 85), (83, 85), (64, 25)]
        draw.polygon(center_peak, fill=crown_gold, outline=electric_blue, width=2)
        
        # Right peak
        right_peak = [(93, 85), (108, 85), (101, 45)]
        draw.polygon(right_peak, fill=crown_gold, outline=electric_blue, width=2)
        
        # Jewels
        draw.ellipse([58, 35, 70, 47], fill=energy_red, outline=deep_black, width=1)  # Center
        draw.ellipse([23, 58, 31, 66], fill=electric_blue, outline=deep_black, width=1)  # Left
        draw.ellipse([97, 58, 105, 66], fill=electric_blue, outline=deep_black, width=1)  # Right
        
        # Save different sizes
        logo_sizes = [
            ("gymratHD_logo.png", (128, 128)),
            ("gymratHD_icon.png", (64, 64)),
            ("gymratHD_small.png", (32, 32))
        ]
        
        for filename, logo_size in logo_sizes:
            if logo_size != size:
                resized = img.resize(logo_size, Image.Resampling.LANCZOS)
                resized.save(filename)
            else:
                img.save(filename)
            print(f"✅ Created: {filename} ({logo_size[0]}x{logo_size[1]})")
        
        print("👑 Beautiful crown logos created successfully!")
        print("🏆 Perfect for the Ultimate Mike Mentzer Tracker!")
        return True
        
    except ImportError:
        print("❌ Pillow not installed")
        print("📦 Install with: pip install pillow")
        return False
    except Exception as e:
        print(f"❌ Logo creation failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🎨 gymratHD Logo Creator")
    print("=" * 50)
    
    success = create_crown_logo()
    
    if success:
        print("\n🏆 LOGO CREATION COMPLETE!")
        print("👑 Crown logos ready for gymratHD")
        print("🎯 Embodying strength and excellence")
    else:
        print("\n⚠️ Logo creation failed")
        print("But gymratHD will still work perfectly!")
    
    print("\n👨‍💻 Created by: github.com/barebonesjones")
    input("\nPress Enter to continue...")