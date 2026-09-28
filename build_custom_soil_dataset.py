"""
========================================================================================
BUILD CUSTOM SOIL DATASET: AUTOMATED SATELLITE FEATURE EXTRACTION PIPELINE
========================================================================================
Purpose:
  This script takes ANY CSV file containing ground-truth soil test points from any country
  (with Latitude, Longitude, and measured N, P, K, pH values) and automatically:
    1. Connects to Microsoft Planetary Computer STAC API.
    2. Searches for cloud-free (< 15% cloud) Sentinel-2 L2A imagery over each coordinate.
    3. Streams the exact pixel surface reflectance for all 10 science bands via rasterio.
    4. Computes 7 scientifically validated soil/canopy spectral indices.
    5. Saves a fully merged, ML-ready CSV table.

Author: Engineering Capstone Project
Supervisor: Dr. Pramod T. C.
========================================================================================
"""

import os
import time
import numpy as np
import pandas as pd
from pystac_client import Client
import planetary_computer as pc
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds

# Initialize Microsoft Planetary Computer STAC Catalog
print("Connecting to Planetary Computer STAC Catalog...")
catalog = Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=pc.sign_inplace,
)

# 10 Science Bands + Scene Classification Layer
SCIENCE_BANDS = ["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12"]


def extract_pixel_at_coord(asset_url: str, lon: float, lat: float) -> float:
    """
    Extracts the surface reflectance value of a single pixel at (lon, lat)
    directly from a Cloud-Optimized GeoTIFF (COG) using rasterio windowing.
    """
    with rasterio.open(asset_url) as src:
        # Transform lat/lon (EPSG:4326) into dataset's native UTM projection
        delta = 0.0001
        bounds_utm = transform_bounds('EPSG:4326', src.crs, lon - delta, lat - delta, lon + delta, lat + delta)
        win = from_bounds(*bounds_utm, transform=src.transform)
        data = src.read(1, window=win)
        val = float(data[0, 0])
        return val


def process_soil_point(lat: float, lon: float, date_range: str = "2024-01-01/2024-06-30"):
    """
    Searches Sentinel-2 for a point, extracts all 10 bands, and calculates spectral indices.
    """
    # 1. Search cloud-free scene
    delta = 0.005 # ~500m search box
    search_bbox = [lon - delta, lat - delta, lon + delta, lat + delta]
    
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=search_bbox,
        datetime=date_range,
        query={"eo:cloud_cover": {"lt": 15}},
        sortby=[{"field": "properties.datetime", "direction": "desc"}]
    )
    
    items = list(search.items())
    if not items:
        # Fallback to wider 12-month window if no scenes found in first window
        search = catalog.search(
            collections=["sentinel-2-l2a"],
            bbox=search_bbox,
            datetime="2023-06-01/2024-06-30",
            query={"eo:cloud_cover": {"lt": 25}},
            sortby=[{"field": "properties.datetime", "direction": "desc"}]
        )
        items = list(search.items())
        if not items:
            print(f"  [!] No cloud-free scene found for Lat: {lat:.4f}, Lon: {lon:.4f}")
            return None

    selected_item = items[0]
    scene_date = selected_item.datetime.strftime("%Y-%m-%d")
    
    # 2. Extract band values
    band_values = {}
    for band in SCIENCE_BANDS:
        url = selected_item.assets[band].href
        raw_val = extract_pixel_at_coord(url, lon, lat)
        # Convert DN to surface reflectance (0.0 to 1.0)
        band_values[band] = raw_val / 10000.0
        
    # Check Scene Classification Layer (SCL)
    scl_url = selected_item.assets["SCL"].href
    scl_val = int(extract_pixel_at_coord(scl_url, lon, lat))
    band_values["SCL"] = scl_val
    band_values["S2_SCENE_DATE"] = scene_date
    
    # 3. Calculate Engineered Spectral Indices
    b2 = band_values["B02"]
    b3 = band_values["B03"]
    b4 = band_values["B04"]
    b5 = band_values["B05"]
    b7 = band_values["B07"]
    b8 = band_values["B08"]
    b8a = band_values["B8A"]
    b11 = band_values["B11"]
    b12 = band_values["B12"]
    
    eps = 1e-6
    # NDVI (Vegetation Index)
    band_values["NDVI"] = (b8 - b4) / (b8 + b4 + eps)
    # BSI (Bare Soil Index)
    band_values["BSI"] = ((b11 + b4) - (b8 + b2)) / ((b11 + b4) + (b8 + b2) + eps)
    # Clay Mineral Ratio (Proxy for Phosphorus & Potassium CEC)
    band_values["Clay_Ratio"] = b11 / (b12 + eps)
    # Ferric Iron Index (Proxy for Phosphorus binding)
    band_values["Ferric_Iron"] = b4 / (b2 + eps)
    # Carbonate Index (Proxy for Soil pH)
    band_values["Carbonate_Index"] = b12 / (b11 + eps)
    # NDRE (Canopy Nitrogen Index)
    band_values["NDRE"] = (b8 - b5) / (b8 + b5 + eps)
    # Soil Brightness Index (Organic Carbon proxy)
    band_values["Soil_Brightness"] = np.sqrt((b4**2 + b3**2 + b8**2) / 3.0)
    
    return band_values


def build_dataset(input_csv_path: str, output_csv_path: str, lat_col: str = "Latitude", lon_col: str = "Longitude"):
    """
    Iterates through each row in the input CSV and builds the ML-ready dataset.
    """
    df_input = pd.read_csv(input_csv_path)
    print(f"Loaded {len(df_input)} soil samples from: {input_csv_path}")
    print(f"Coordinates columns: '{lat_col}', '{lon_col}'")
    
    results = []
    
    for idx, row in df_input.iterrows():
        lat = float(row[lat_col])
        lon = float(row[lon_col])
        print(f"\nProcessing Point {idx + 1}/{len(df_input)}: Lat {lat:.4f}, Lon {lon:.4f}...")
        
        try:
            satellite_data = process_soil_point(lat, lon)
            if satellite_data is not None:
                # Merge original ground-truth columns with extracted satellite features
                combined_row = row.to_dict()
                combined_row.update(satellite_data)
                results.append(combined_row)
                print(f"  [OK] Scene Date: {satellite_data['S2_SCENE_DATE']} | SCL: {satellite_data['SCL']} | NDVI: {satellite_data['NDVI']:.3f} | BSI: {satellite_data['BSI']:.3f}")
            else:
                print("  [SKIP] Could not fetch valid satellite data.")
        except Exception as e:
            print(f"  [ERROR] {e}")
            
    df_out = pd.DataFrame(results)
    df_out.to_csv(output_csv_path, index=False)
    print(f"\n==================================================================")
    print(f"SUCCESS! Created custom dataset with {len(df_out)} paired samples.")
    print(f"Saved to: {output_csv_path}")
    print(f"==================================================================")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build Custom Soil Dataset from Satellite Imagery")
    parser.add_argument("--input", "-i", type=str, default="sample_indian_soil_points.csv", help="Input CSV path")
    parser.add_argument("--output", "-o", type=str, default="custom_soil_dataset_ready_for_training.csv", help="Output CSV path")
    parser.add_argument("--lat", type=str, default="Latitude", help="Name of Latitude column")
    parser.add_argument("--lon", type=str, default="Longitude", help="Name of Longitude column")
    args = parser.parse_args()
    
    build_dataset(args.input, args.output, args.lat, args.lon)
