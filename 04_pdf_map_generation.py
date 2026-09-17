import arcpy
import re
from pathlib import Path

def get_combined_extent(shp_files):
    x_mins, y_mins, x_maxs, y_maxs = [], [], [], []
    for shp in shp_files:
        desc = arcpy.Describe(str(shp))
        ext = desc.extent
        x_mins.append(ext.XMin)
        y_mins.append(ext.YMin)
        x_maxs.append(ext.XMax)
        y_maxs.append(ext.YMax)
    return arcpy.Extent(min(x_mins), min(y_mins), max(x_maxs), max(y_maxs))

def choose_scale_and_paper(extent):
    width = extent.width
    height = extent.height
    max_dim = max(width, height)
    
    # Validation constraint from your logs
    if max_dim > 15000:
        raise RuntimeError("Village cannot fit. Please check the shapefiles for stray geometries located far from the main area.")
        
    if max_dim > 8000:
        return "1:10,000", "A0 Landscape"
    elif max_dim > 5000:
        return "1:8,000", "A1 Landscape"
    elif max_dim > 3000:
        return "1:8,000", "A2 Landscape"
    else:
        return "1:8,000", "A3 Landscape"

def export_village_maps(root_path):
    root_dir = Path(root_path)
    print("\n==============================================================================")
    print("PROFESSIONAL VILLAGE CADASTRAL EXPORT")
    print("==============================================================================")

    code_pattern = re.compile(r"^(\d{6})_(.*)")

    for taluka in root_dir.iterdir():
        if taluka.is_dir():
            for village in taluka.iterdir():
                if village.is_dir():
                    shape_folder = village / "Pandan_Georeff" / "04_Shape"
                    pdf_folder = village / "Pandan_Georeff" / "07_PDF Map"
                    
                    match = code_pattern.match(village.name)
                    if not match:
                        continue
                        
                    lgd_code = match.group(1)
                    village_name = match.group(2).strip()
                    
                    shp_files = list(shape_folder.glob("*.shp"))
                    if not shape_folder.exists() or not shp_files:
                        continue

                    print(f"\n==============================================================================")
                    print(f"PROCESSING: {shape_folder}")
                    print("==============================================================================")
                    print(f"  Village : {village_name}")
                    print(f"  LGD Code: {lgd_code}")
                    print(f"  Taluka  : {taluka.name}")
                    
                    try:
                        pdf_folder.mkdir(exist_ok=True)
                        output_pdf = pdf_folder / f"{lgd_code}_{village_name}.pdf"
                        
                        ext = get_combined_extent(shp_files)
                        scale, paper = choose_scale_and_paper(ext)
                        
                        # Add your arcpy.mp layout export call here utilizing the 
                        # dynamically calculated 'scale' and 'paper' variables
                        
                        print(f"  Scale : {scale}")
                        print(f"  Paper : {paper}")
                        print(f"  SUCCESS: {output_pdf}")
                        
                    except RuntimeError as re_err:
                        print(f"  ERROR: {str(re_err)}")
                    except Exception as e:
                        print(f"  ERROR: {str(e)}")

if __name__ == "__main__":
    db_root = r"E:\01.FInal Database\V1 Pandan Raste Structured Format\Pandan Raste"
    export_village_maps(db_root)
