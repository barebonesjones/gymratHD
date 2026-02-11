diff --git a/create_logo.py b/create_logo.py
index ba5923cf5fc0f28cfdf826beeacd6a3e60d3a48f..f853a95e5f03521c9b598e46b1536e420f09e97b 100644
--- a/create_logo.py
+++ b/create_logo.py
@@ -1,35 +1,37 @@
 """
 gymratHD Logo Creator v1.0
 ===========================
 
 Creates beautiful crown logos with zero errors.
 Simple, reliable, works every time.
 
 Created by: github.com/barebonesjones
 """
 
+import sys
+
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
@@ -68,26 +70,29 @@ def create_crown_logo():
         
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
-    input("\nPress Enter to continue...")
\ No newline at end of file
+
+    # Avoid blocking/EOF failures when run by installers or CI without a TTY.
+    if sys.stdin.isatty():
+        input("\nPress Enter to continue...")
