"""
02_shp_to_json.py
Iterates through the '04_Shape' folders in the Pandan Raste directory
and converts Line and Polygon shapefiles to GeoJSON format.
"""

from pathlib import Path
# import geopandas as gpd  # Uncomment if using geopandas
# import arcpy             # Uncomment if using arcpy

def convert_shp_to_geojson(root_path):
    root_dir = Path(root_path)
    print(f"Searching for '04_Shape' folders in: {root_dir}\n")

    for taluka in root_dir.iterdir():
        if taluka.is_dir():
            for village in taluka.iterdir():
                if village.is_dir():
                    shape_folder = village / "Pandan_Georeff" / "04_Shape"
                    
                    if shape_folder.exists() and shape_folder.is_dir():
                        print(f"Processing: {shape_folder}")
                        
                        for shp_file in shape_folder.glob("*.shp"):
                            geojson_name = shp_file.with_suffix('.geojson').name
                            geojson_path = shape_folder / geojson_name
                            
                            print(f"  Converting: {shp_file.name} -> {geojson_name}")
                            
                            try:
                                # ----------------------------------------------------
                                # INSERT YOUR CONVERSION LOGIC HERE (e.g., geopandas)
                                # gdf = gpd.read_file(shp_file)
                                # gdf.to_file(geojson_path, driver='GeoJSON')
                                # ----------------------------------------------------
                                print("    -> Success!")
                            except Exception as e:
                                print(f"    -> Failed! Error: {e}")

if __name__ == "__main__":
    db_root = r"E:\01.FInal Database\V1 Pandan Raste Structured Format\Pandan Raste"
    convert_shp_to_geojson(db_root)
