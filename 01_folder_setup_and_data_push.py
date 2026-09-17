"""
01_folder_setup_and_data_push.py
Handles the creation of the Pandan_Georeff directory structure,
cleans up legacy folders, and migrates raw data into the new structure.
"""

import shutil
import csv
import re
from pathlib import Path

def create_base_structure(root_path):
    print("--- Step 1: Creating Pandan_Georeff Folders ---")
    for taluka_folder in root_path.iterdir():
        if taluka_folder.is_dir():
            for village_folder in taluka_folder.iterdir():
                if village_folder.is_dir():
                    georeff_folder = village_folder / "Pandan_Georeff"
                    georeff_folder.mkdir(exist_ok=True)
                    
                    for item in village_folder.iterdir():
                        if item.name == "Pandan_Georeff":
                            continue
                        try:
                            shutil.move(str(item), str(georeff_folder))
                        except Exception as e:
                            print(f"Error moving {item.name}: {e}")

def cleanup_survey_maps(comp_root_path):
    print("\n--- Step 2: Deleting Survey Maps Folders ---")
    for taluka_folder in comp_root_path.iterdir():
        if taluka_folder.is_dir():
            survey_maps_folder = taluka_folder / "Survey Maps"
            if survey_maps_folder.exists() and survey_maps_folder.is_dir():
                try:
                    shutil.rmtree(survey_maps_folder)
                    print(f"Deleted: '{survey_maps_folder}'")
                except Exception as e:
                    print(f"Error deleting '{survey_maps_folder}': {e}")

def create_subfolders(root_path):
    print("\n--- Step 3: Creating Subfolders and Moving Shapefiles ---")
    new_folders = ["01_Scan Image", "03_Drawing", "04_Shape", "DWG To SHP"]
    for taluka_folder in root_path.iterdir():
        if taluka_folder.is_dir():
            for village_folder in taluka_folder.iterdir():
                if village_folder.is_dir():
                    georeff_folder = village_folder / "Pandan_Georeff"
                    if georeff_folder.exists() and georeff_folder.is_dir():
                        for folder_name in new_folders:
                            (georeff_folder / folder_name).mkdir(exist_ok=True)
                        
                        shape_folder_path = georeff_folder / "04_Shape"
                        for item in georeff_folder.iterdir():
                            if item.name in new_folders:
                                continue
                            try:
                                shutil.move(str(item), str(shape_folder_path))
                            except Exception as e:
                                print(f"Error moving '{item.name}': {e}")

def migrate_pointline_data(source_root, dest_root, csv_report_path):
    print("\n--- Step 4: Migrating Pointline Data ---")
    code_pattern = re.compile(r"^(\d{6})")
    dest_villages = {}
    
    if dest_root.exists():
        for taluka in dest_root.iterdir():
            if taluka.is_dir():
                for village in taluka.iterdir():
                    if village.is_dir():
                        match = code_pattern.match(village.name)
                        if match:
                            dest_villages[match.group(1)] = village

    report_data = []
    if source_root.exists():
        for taluka in source_root.iterdir():
            if taluka.is_dir():
                prachalit_maps = taluka / "Prachalit Maps"
                villages_parent = prachalit_maps if prachalit_maps.exists() else taluka
                
                for src_village in villages_parent.iterdir():
                    if src_village.is_dir():
                        match = code_pattern.match(src_village.name)
                        if match:
                            village_code = match.group(1)
                            if village_code in dest_villages:
                                dest_village_path = dest_villages[village_code]
                                target_folder = dest_village_path / "Pandan_Georeff" / "DWG To SHP"
                                target_folder.mkdir(parents=True, exist_ok=True)
                                
                                try:
                                    items_copied = 0
                                    for item in src_village.iterdir():
                                        if item.is_file():
                                            shutil.copy2(item, target_folder)
                                        elif item.is_dir():
                                            shutil.copytree(item, target_folder / item.name, dirs_exist_ok=True)
                                        items_copied += 1
                                    
                                    status, note = ("Success", f"Copied {items_copied} items") if items_copied > 0 else ("Skipped", "Empty source")
                                    report_data.append([village_code, src_village.name, dest_village_path.name, status, note])
                                except Exception as e:
                                    report_data.append([village_code, src_village.name, dest_village_path.name, "Failed", str(e)])
                            else:
                                report_data.append([village_code, src_village.name, "N/A", "Failed", "No matching village code"])

    with open(csv_report_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Village_Code", "Source_Folder", "Destination_Folder", "Status", "Remarks"])
        writer.writerows(report_data)

def migrate_jpg_dwg_data(source_root, dest_root, csv_report_path):
    print("\n--- Step 5: Migrating JPG and DWG Data ---")
    code_pattern = re.compile(r"^(\d{6})")
    image_extensions = {".jpg", ".jpeg", ".png"}
    dest_villages = {}
    
    if dest_root.exists():
        for taluka in dest_root.iterdir():
            if taluka.is_dir():
                for village in taluka.iterdir():
                    if village.is_dir():
                        match = code_pattern.match(village.name)
                        if match:
                            dest_villages[match.group(1)] = village

    report_data = []
    if source_root.exists():
        for taluka in source_root.iterdir():
            if taluka.is_dir():
                prachalit_maps = taluka / "Prachalit Maps"
                villages_parent = prachalit_maps if prachalit_maps.exists() else taluka
                
                for src_village in villages_parent.iterdir():
                    if src_village.is_dir():
                        match = code_pattern.match(src_village.name)
                        if match:
                            village_code = match.group(1)
                            if village_code in dest_villages:
                                dest_village_path = dest_villages[village_code]
                                target_scan = dest_village_path / "Pandan_Georeff" / "01_Scan Image"
                                target_dwg = dest_village_path / "Pandan_Georeff" / "03_Drawing"
                                
                                target_scan.mkdir(parents=True, exist_ok=True)
                                target_dwg.mkdir(parents=True, exist_ok=True)
                                
                                images_copied, dwgs_copied = 0, 0
                                try:
                                    for item in src_village.rglob("*"):
                                        if item.is_file():
                                            if item.suffix.lower() in image_extensions:
                                                shutil.copy2(item, target_scan)
                                                images_copied += 1
                                            else:
                                                shutil.copy2(item, target_dwg)
                                                dwgs_copied += 1
                                    
                                    if (images_copied + dwgs_copied) > 0:
                                        report_data.append([village_code, src_village.name, dest_village_path.name, "Success", f"{images_copied} Img, {dwgs_copied} DWG"])
                                    else:
                                        report_data.append([village_code, src_village.name, dest_village_path.name, "Skipped", "No files found"])
                                except Exception as e:
                                    report_data.append([village_code, src_village.name, dest_village_path.name, "Failed", str(e)])
                            else:
                                report_data.append([village_code, src_village.name, "N/A", "Failed", "No match"])

    with open(csv_report_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Village_Code", "Source_Folder", "Destination_Folder", "Status", "Remarks"])
        writer.writerows(report_data)

if __name__ == "__main__":
    # UPDATE DIRECTORIES HERE
    main_root = Path(r"D:\New folder")
    comp_root = Path(r"D:\03_Comp")
    pt_line_source = Path(r"D:\Data Migration\Pointline data")
    pandan_dest = Path(r"D:\Data Migration\Pandan Raste")
    scan_dwg_source = Path(r"D:\Data Migration\DWG and Scan Image")
    
    csv_pt_line = Path(r"D:\Data Migration\Copy_Report.csv")
    csv_scan_dwg = Path(r"D:\Data Migration\Data_Migration_Report.csv")

    create_base_structure(main_root)
    cleanup_survey_maps(comp_root)
    create_subfolders(main_root)
    migrate_pointline_data(pt_line_source, pandan_dest, csv_pt_line)
    migrate_jpg_dwg_data(scan_dwg_source, pandan_dest, csv_scan_dwg)
