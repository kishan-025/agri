"""
Generate realistic, high-resolution visual imagery assets for the presentation slides
matching the modern, aesthetic styling of the Gamma presentation.
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import matplotlib.pyplot as plt

assets_dir = r"c:\Users\kisha\OneDrive\Desktop\agri\assets"
os.makedirs(assets_dir, exist_ok=True)

# 1. Generate Aerial Satellite Farm Field Image (Split Screen for Title Slide)
def create_aerial_farm():
    width, height = 900, 1400
    img = Image.new("RGB", (width, height), (35, 75, 45))
    draw = ImageDraw.Draw(img)
    
    # Draw organic agricultural field boundaries and textures
    np.random.seed(42)
    # Left half: bare plowed soil (shades of warm ochre, sienna, and brown)
    for y in range(0, height, 8):
        shade = int(140 + 35 * np.sin(y / 40.0) + np.random.randint(-15, 15))
        r = min(255, shade + 35)
        g = min(255, shade + 5)
        b = max(0, shade - 45)
        # Plow line angle
        x_split = int(480 + 80 * np.sin(y / 150.0) + 20 * np.cos(y / 50.0))
        draw.rectangle([0, y, x_split, y + 8], fill=(r, g, b))
        
    # Right half: lush green crops (shades of deep emerald, forest, and olive green)
    for y in range(0, height, 8):
        x_split = int(480 + 80 * np.sin(y / 150.0) + 20 * np.cos(y / 50.0))
        shade = int(90 + 30 * np.sin(y / 30.0) + np.random.randint(-10, 10))
        r = max(0, shade - 50)
        g = min(255, shade + 35)
        b = max(0, shade - 40)
        draw.rectangle([x_split, y, width, y + 8], fill=(r, g, b))
        
    # Soft blur to simulate optical satellite sensor capture
    img = img.filter(ImageFilter.GaussianBlur(radius=2.5))
    img.save(os.path.join(assets_dir, "aerial_farm_split.png"), quality=95)
    print("Created aerial_farm_split.png")

# 2. Generate Satellite Agricultural Landscape Image (for Proposed Solution & Footer)
def create_satellite_landscape():
    width, height = 1200, 750
    img = Image.new("RGB", (width, height), (40, 85, 50))
    draw = ImageDraw.Draw(img)
    
    # Draw geometric field parcels
    colors = [
        (160, 130, 95),  # tilled bare soil
        (135, 105, 75),  # dark organic soil
        (50, 120, 60),   # dense crop
        (85, 150, 70),   # wheat canopy
        (65, 135, 65),   # mature crop
        (175, 150, 110), # sandy loam
        (45, 100, 55)    # orchards
    ]
    np.random.seed(101)
    grid_x = 8
    grid_y = 6
    dx = width // grid_x
    dy = height // grid_y
    for i in range(grid_x):
        for j in range(grid_y):
            c = colors[np.random.randint(len(colors))]
            x0 = i * dx + np.random.randint(-10, 10)
            y0 = j * dy + np.random.randint(-10, 10)
            x1 = x0 + dx + 15
            y1 = y0 + dy + 15
            draw.rectangle([x0, y0, x1, y1], fill=c, outline=(220, 220, 220), width=1)
            
    img = img.filter(ImageFilter.GaussianBlur(radius=1.8))
    img.save(os.path.join(assets_dir, "satellite_fields.png"), quality=95)
    print("Created satellite_fields.png")

# 3. Generate Laboratory Soil Sample Petri Dishes (for Limitations Slide)
def create_soil_lab_samples():
    width, height = 800, 1000
    img = Image.new("RGB", (width, height), (235, 240, 242)) # lab bench background
    draw = ImageDraw.Draw(img)
    
    # Draw circular petri dishes with varying soil colors
    soil_colors = [
        (70, 50, 40),   # High organic matter (dark brown/black)
        (185, 150, 110), # Sandy soil (light tan)
        (150, 75, 50),   # Red soil (ferric oxide rich)
        (120, 100, 80),  # Loamy soil
        (160, 140, 120), # Silt loam
        (90, 70, 55),    # Clay loam
        (200, 175, 130), # Calcareous soil
        (140, 60, 40),   # Laterite soil
        (110, 95, 75)    # Alluvial soil
    ]
    
    centers = [
        (250, 200), (550, 220),
        (180, 420), (420, 440), (660, 410),
        (220, 660), (480, 680),
        (300, 880), (580, 890)
    ]
    
    radius = 95
    for (cx, cy), col in zip(centers, soil_colors):
        # Outer petri dish glass border
        draw.ellipse([cx - radius - 8, cy - radius - 8, cx + radius + 8, cy + radius + 8], fill=(220, 228, 232), outline=(180, 195, 205), width=3)
        # Inner soil texture
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=col)
        # Add subtle glass reflection highlight
        draw.arc([cx - radius + 5, cy - radius + 5, cx + radius - 5, cy + radius - 5], start=210, end=330, fill=(255, 255, 255), width=4)
        
    img = img.filter(ImageFilter.GaussianBlur(radius=1.2))
    img.save(os.path.join(assets_dir, "soil_lab_samples.png"), quality=95)
    print("Created soil_lab_samples.png")

if __name__ == "__main__":
    create_aerial_farm()
    create_satellite_landscape()
    create_soil_lab_samples()
