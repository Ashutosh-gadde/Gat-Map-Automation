import arcpy
from pathlib import Path

def auto_detect_and_match_crs(root_path):
    root_dir = Path(root_path)
    
    # Define standard reference CRS for the region
    GCS_WGS84 = arcpy.SpatialReference(4326)    # EPSG: 4326 (Degrees)
    UTM_ZONE_43N = arcpy.SpatialReference(32643) # EPSG: 32643 (Meters)

    print(f"Starting Auto-Detection & Matching in: {root_dir}\n")

    total_matched = 0
    total_reprojected = 0
    total_skipped = 0
    total_errors = 0

    for taluka in root_dir.iterdir():
        if not taluka.is_dir():
            continue

        print("=" * 50)
        print(f" Processing Taluka: {taluka.name}")
        print("=" * 50)

        for village in taluka.iterdir():
            if not village.is_dir():
                continue

            # 1. Find Reference Shapefile
            shape_folder = village / "Pandan_Georeff" / "04_Shape"
            shp_files = list(shape_folder.glob("*.shp")) if shape_folder.exists() else []
            if not shp_files:
                shp_files = list(village.rglob("*.shp"))

            if not shp_files:
                print(f"  [SKIP] {village.name}: No shapefiles found.")
                total_skipped += 1
                continue

            try:
                # Determine Shapefile CRS and Extent
                ref_shp = str(shp_files[0])
                shp_desc = arcpy.Describe(ref_shp)
                shp_sr = shp_desc.spatialReference
                shp_ext = shp_desc.extent

                # Auto-determine Shapefile's true target CRS
                if shp_sr and shp_sr.name.upper() != "UNKNOWN":
                    target_sr = shp_sr
                else:
                    target_sr = GCS_WGS84 if shp_ext.XMax < 180 else UTM_ZONE_43N
                    arcpy.DefineProjection_management(ref_shp, target_sr)

                # 2. Locate '06_Recified Image' folder
                rectified_folders = [
                    d for d in village.rglob("*") 
                    if d.is_dir() and d.name.lower() in ["06_recified image", "06_rectified image"]
                ]

                if not rectified_folders:
                    print(f"  [SKIP] {village.name}: '06_Recified Image' folder not found.")
                    total_skipped += 1
                    continue

                for rect_dir in rectified_folders:
                    tif_files = list(rect_dir.glob("*.tif"))
                    for tif in tif_files:
                        tif_path = str(tif)
                        tif_desc = arcpy.Describe(tif_path)
                        tif_ext = tif_desc.extent

                        # Detect native raster coordinate system based on extent values
                        is_raster_degrees = tif_ext.XMax < 180
                        is_target_degrees = target_sr.type == "Geographic" or target_sr.factoryCode == 4326

                        native_sr = GCS_WGS84 if is_raster_degrees else UTM_ZONE_43N

                        # Step A: Define the true native projection on the raster header
                        arcpy.DefineProjection_management(tif_path, native_sr)

                        # Step B: Match Raster to Target Shapefile
                        if is_raster_degrees == is_target_degrees:
                            # Units match (both Degrees or both Meters)
                            arcpy.DefineProjection_management(tif_path, target_sr)
                            print(f"  [MATCHED] {village.name} -> {tif.name} ({target_sr.name})")
                            total_matched += 1
                        else:
                            # Units mismatch -> Reproject raster pixels to match Shapefile
                            print(f"  [REPROJECTING] {village.name} -> {tif.name} ({native_sr.name} -> {target_sr.name})")
                            
                            temp_tif = tif.parent / f"temp_{tif.name}"
                            arcpy.management.ProjectRaster(
                                in_raster=tif_path,
                                out_raster=str(temp_tif),
                                out_coor_system=target_sr,
                                resampling_type="NEAREST"
                            )
                            arcpy.management.Delete(tif_path)
                            arcpy.management.Rename(str(temp_tif), tif_path)
                            print(f"  [REPROJECTED & MATCHED] {village.name} -> {tif.name}")
                            total_reprojected += 1

            except Exception as e:
                print(f"  [ERROR] {village.name}: {str(e)}")
                total_errors += 1

    print("\n" + "=" * 50)
    print("PROCESS COMPLETE")
    print(f"Directly Matched:   {total_matched} TIFFs")
    print(f"Reprojected:        {total_reprojected} TIFFs")
    print(f"Skipped Villages:   {total_skipped}")
    print(f"Errors Encountered: {total_errors}")
    print("=" * 50)

if __name__ == "__main__":
    db_root = r"E:\01.FInal Database\V1 Pandan Raste Structured Format\Pandan Raste"
    auto_detect_and_match_crs(db_root)
