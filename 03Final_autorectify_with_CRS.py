import arcpy
from pathlib import Path

# ==============================================================================
# GLOBAL CONFIGURATION
# ==============================================================================
MAP_BUFFER_PERCENT = 10
TARGET_EPSG = 32643  # WGS 1984 UTM Zone 43N (Standard for Maharashtra)
GCS_EPSG = 4326     # GCS WGS 1984 (Degrees)


def get_combined_extent(shp_files):
    """Calculates the bounding envelope of multiple shapefiles."""
    x_mins, y_mins, x_maxs, y_maxs = [], [], [], []
    for shp in shp_files:
        desc = arcpy.Describe(str(shp))
        ext = desc.extent
        x_mins.append(ext.XMin)
        y_mins.append(ext.YMin)
        x_maxs.append(ext.XMax)
        y_maxs.append(ext.YMax)
    
    if not x_mins:
        raise ValueError("No valid shapefile geometry found for extent calculation.")
        
    return arcpy.Extent(min(x_mins), min(y_mins), max(x_maxs), max(y_maxs))


def buffer_extent(extent, percent):
    """Adds a percentage buffer around a bounding extent."""
    width = extent.width
    height = extent.height
    x_buf = width * (percent / 100.0)
    y_buf = height * (percent / 100.0)
    return arcpy.Extent(
        extent.XMin - x_buf, 
        extent.YMin - y_buf, 
        extent.XMax + x_buf, 
        extent.YMax + y_buf
    )


def standardize_vector_crs(shp_path, target_sr):
    """Auto-detects shapefile CRS and converts to target UTM Zone 43N if needed."""
    desc = arcpy.Describe(shp_path)
    sr = desc.spatialReference
    ext = desc.extent

    # If projection is missing, assign GCS if coordinates < 180, else target UTM
    if not sr or sr.name.upper() == "UNKNOWN":
        base_sr = arcpy.SpatialReference(GCS_EPSG) if ext.XMax < 180 else target_sr
        arcpy.DefineProjection_management(shp_path, base_sr)
        sr = arcpy.Describe(shp_path).spatialReference

    # Reproject if in Degrees (GCS)
    if ext.XMax < 180 or sr.type == "Geographic":
        temp_shp = str(Path(shp_path).parent / f"temp_{Path(shp_path).name}")
        arcpy.management.Project(shp_path, temp_shp, target_sr)
        arcpy.management.Delete(shp_path)
        arcpy.management.Rename(temp_shp, shp_path)
        return True
    return False


def standardize_raster_crs(tif_path, target_sr):
    """Auto-detects raster CRS and reprojects to target UTM Zone 43N if in degrees."""
    desc = arcpy.Describe(tif_path)
    sr = desc.spatialReference
    ext = desc.extent

    # If projection is missing, assign base projection first
    if not sr or sr.name.upper() == "UNKNOWN":
        base_sr = arcpy.SpatialReference(GCS_EPSG) if ext.XMax < 180 else target_sr
        arcpy.DefineProjection_management(tif_path, base_sr)
        sr = arcpy.Describe(tif_path).spatialReference

    # Reproject if in Degrees (GCS) to UTM Meters
    if ext.XMax < 180 or sr.type == "Geographic":
        temp_tif = str(Path(tif_path).parent / f"temp_{Path(tif_path).name}")
        arcpy.management.ProjectRaster(
            in_raster=tif_path,
            out_raster=temp_tif,
            out_coor_system=target_sr,
            resampling_type="NEAREST"  # Preserves exact line/color index values
        )
        arcpy.management.Delete(tif_path)
        arcpy.management.Rename(temp_tif, tif_path)
        return True
    else:
        # Enforce header stamp if already in meters
        arcpy.DefineProjection_management(tif_path, target_sr)
        return False


def process_district_rectification(root_path, target_epsg=TARGET_EPSG):
    """Master workflow to process rectification extents and standardize CRS across all villages."""
    root_dir = Path(root_path)
    target_sr = arcpy.SpatialReference(target_epsg)

    print(f"==================================================")
    print(f" STARTING DISTRICT BATCH PROCESS")
    print(f" Target Root: {root_dir}")
    print(f" Enforced CRS: {target_sr.name} (EPSG: {target_epsg})")
    print(f"==================================================\n")

    total_villages = 0
    total_shps_standardized = 0
    total_tiffs_standardized = 0
    total_skipped = 0
    total_errors = 0

    for taluka in root_dir.iterdir():
        if not taluka.is_dir():
            continue

        print(f"\n--- Processing Taluka: {taluka.name} ---")

        for village in taluka.iterdir():
            if not village.is_dir():
                continue

            total_villages += 1
            print(f"\n[Village {total_villages}] {village.name}")

            try:
                # -------------------------------------------------------------
                # 1. SHAPEFILE PROCESSING & EXTENT COMPUTATION
                # -------------------------------------------------------------
                shape_folder = village / "Pandan_Georeff" / "04_Shape"
                shp_files = list(shape_folder.glob("*.shp")) if shape_folder.exists() else list(village.rglob("*.shp"))

                if not shp_files:
                    print(f"   -> [SKIP] Missing reference shapefiles in '04_Shape'.")
                    total_skipped += 1
                    continue

                # Standardize vector shapefiles to UTM Zone 43N
                for shp in shp_files:
                    if standardize_vector_crs(str(shp), target_sr):
                        total_shps_standardized += 1

                # Calculate buffered extent for rectification boundary
                target_shps = [
                    str(s) for s in shp_files 
                    if "_lines" in s.name.lower() or "_polygons" in s.name.lower()
                ] or [str(s) for s in shp_files]

                combined_ext = get_combined_extent(target_shps)
                buffered_ext = buffer_extent(combined_ext, MAP_BUFFER_PERCENT)
                
                print(f"   -> Calculated Extent (Buffered {MAP_BUFFER_PERCENT}%):")
                print(f"      XMin: {buffered_ext.XMin:.2f}, YMin: {buffered_ext.YMin:.2f}")
                print(f"      XMax: {buffered_ext.XMax:.2f}, YMax: {buffered_ext.YMax:.2f}")

                # -------------------------------------------------------------
                # 2. RECTIFIED IMAGE STANDARDIZATION ('06_Recified Image')
                # -------------------------------------------------------------
                rectified_folders = [
                    d for d in village.rglob("*") 
                    if d.is_dir() and d.name.lower() in ["06_recified image", "06_rectified image"]
                ]

                if not rectified_folders:
                    print(f"   -> [SKIP] Folder '06_Recified Image' not found.")
                    total_skipped += 1
                    continue

                tif_found = False
                for rect_dir in rectified_folders:
                    tif_files = list(rect_dir.glob("*.tif"))
                    for tif in tif_files:
                        tif_found = True
                        tif_path = str(tif)
                        
                        # Apply transformation/standardization logic
                        if standardize_raster_crs(tif_path, target_sr):
                            print(f"   -> [REPROJECTED TIFF] {tif.name} -> {target_sr.name}")
                            total_tiffs_standardized += 1
                        else:
                            print(f"   -> [VERIFIED TIFF] {tif.name} matches {target_sr.name}")

                if not tif_found:
                    print(f"   -> [SKIP] No .tif files found inside '06_Recified Image'.")
                    total_skipped += 1

            except Exception as e:
                print(f"   -> [ERROR] Failed to process {village.name}: {str(e)}")
                total_errors += 1

    # -------------------------------------------------------------------------
    # SUMMARY LOG
    # -------------------------------------------------------------------------
    print("\n" + "=" * 50)
    print(" BATCH EXECUTION COMPLETE")
    print("=" * 50)
    print(f" Total Villages Evaluated:  {total_villages}")
    print(f" Shapefiles Standardized:   {total_shps_standardized}")
    print(f" TIFFs Standardized:        {total_tiffs_standardized}")
    print(f" Skipped Items/Folders:     {total_skipped}")
    print(f" Errors Encountered:        {total_errors}")
    print("=" * 50)


if __name__ == "__main__":
    # Define District Root Folder Path
    db_root = r"E:\01.FInal Database\V1 Pandan Raste Structured Format\Pandan Raste"
    
    # Run master rectification & standardization process
    process_district_rectification(db_root, target_epsg=32643)
