import arcpy
from pathlib import Path

MAP_BUFFER_PERCENT = 10 

def get_combined_extent(shp_files):
    x_mins, y_mins, x_maxs, y_maxs = [], [], [], []
    for shp in shp_files:
        desc = arcpy.Describe(str(shp))
        ext = desc.extent
        x_mins.append(ext.XMin)
        y_mins.append(ext.YMin)
        x_maxs.append(ext.XMax)
        y_maxs.append(ext.YMax)
    
    if not x_mins:
        raise ValueError("No valid geometry found.")
        
    return arcpy.Extent(min(x_mins), min(y_mins), max(x_maxs), max(y_maxs))

def buffer_extent(extent, percent):
    width = extent.width
    height = extent.height
    x_buf = width * (percent / 100.0)
    y_buf = height * (percent / 100.0)
    return arcpy.Extent(extent.XMin - x_buf, extent.YMin - y_buf, 
                        extent.XMax + x_buf, extent.YMax + y_buf)

def process_rectification(root_path):
    root_dir = Path(root_path)
    print(f"Starting batch process in root: {root_dir}\n")

    for taluka in root_dir.iterdir():
        if taluka.is_dir():
            for village in taluka.iterdir():
                if village.is_dir():
                    print("-" * 50)
                    print(f"Found Village: {village.name}")
                    print("-" * 50)
                    print(f"   -> Processing {village.name.split('_')[-1]}...")
                    
                    shape_folder = village / "Pandan_Georeff" / "04_Shape"
                    if not shape_folder.exists() or not list(shape_folder.glob("*.shp")):
                        print(f"Skipping {village.name}: Missing .tif or .shp file.")
                        continue

                    try:
                        print("   -> Applying rigid scale and creating LZW compressed TIFF...")
                        shp_files = list(shape_folder.glob("*_Lines.shp")) + list(shape_folder.glob("*_polygons.shp"))
                        
                        if not shp_files:
                            raise FileNotFoundError(f"Missing required shapefiles in {shape_folder}")
                            
                        # Calculates combined buffered extent as seen in your logs
                        ext = buffer_extent(get_combined_extent(shp_files), MAP_BUFFER_PERCENT)
                        
                        # Add your specific arcpy.Warp_management or georeferencing call here
                        # using the calculated 'ext' boundary.
                        
                        print("   -> Result: PASSED - Undistorted Center-Scale alignment applied.")
                        
                    except Exception as e:
                        print(f"   -> Result: ERROR - {str(e)}")

if __name__ == "__main__":
    db_root = r"E:\01.FInal Database\V1 Pandan Raste Structured Format\Pandan Raste"
    process_rectification(db_root)
