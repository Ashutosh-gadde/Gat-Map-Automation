import arcpy
import os
import csv
import tkinter as tk
from tkinter import filedialog

arcpy.env.overwriteOutput = True

# -------------------------------
# Folder selection
# -------------------------------
root = tk.Tk()
root.withdraw()

input_folder = filedialog.askdirectory(title="Select Input Folder")
output_folder = filedialog.askdirectory(title="Select Output Folder")

if not input_folder or not output_folder:
    print("❌ Folder not selected")
    raise SystemExit

os.makedirs(output_folder, exist_ok=True)
csv_path = os.path.join(output_folder, "Topology_QC_Final.csv")
final_rows = []

# -------------------------------
# Scan folders
# -------------------------------
for root_dir, dirs, files in os.walk(input_folder):
    for file in files:
        if file.endswith("_polygons.shp"):

            village_full = file.replace("_polygons.shp", "")
            fc = os.path.join(root_dir, file)

            print(f"Processing: {village_full}")

            # Split LGD + Name
            parts = village_full.split("_")
            if len(parts) >= 2:
                lgd = parts[0]
                name = "_".join(parts[1:])
            else:
                lgd = village_full
                name = village_full

            # ---------------- BLANK ----------------
            blank_count = 0
            with arcpy.da.SearchCursor(fc, ["SHAPE@"]) as cursor:
                for row in cursor:
                    geom = row[0]
                    if geom is None or geom.area == 0:
                        blank_count += 1

            # ---------------- OVERLAP ----------------
            overlap_fc = os.path.join(output_folder, village_full + "_OVERLAP.shp")
            intersect_fc = "in_memory\\intersect_tmp"

            arcpy.Intersect_analysis([fc, fc], intersect_fc)

            fields = arcpy.ListFields(intersect_fc)
            fid_fields = [f.name for f in fields if f.name.startswith("FID_")]

            overlap_count = 0

            if len(fid_fields) >= 2:
                query = f"{fid_fields[0]} <> {fid_fields[1]}"

                if arcpy.Exists("int_lyr"):
                    arcpy.Delete_management("int_lyr")

                arcpy.MakeFeatureLayer_management(intersect_fc, "int_lyr")
                arcpy.SelectLayerByAttribute_management("int_lyr", "NEW_SELECTION", query)

                overlap_count = int(arcpy.GetCount_management("int_lyr")[0])

                if overlap_count > 0:
                    arcpy.CopyFeatures_management("int_lyr", overlap_fc)

            # ---------------- GAP ----------------
            # Using in_memory workspace for faster processing and to avoid cluttering the output folder
            dissolve_fc = "in_memory\\dissolve_tmp"
            line_fc = "in_memory\\line_tmp"
            poly_fc = "in_memory\\poly_tmp"
            gap_fc = os.path.join(output_folder, village_full + "_GAP.shp")

            arcpy.Dissolve_management(fc, dissolve_fc)
            arcpy.PolygonToLine_management(dissolve_fc, line_fc)
            arcpy.FeatureToPolygon_management(line_fc, poly_fc)
            arcpy.Erase_analysis(poly_fc, fc, gap_fc)

            gap_count = int(arcpy.GetCount_management(gap_fc)[0])
            
            # Clean up empty gap shapefiles to save space
            if gap_count == 0 and arcpy.Exists(gap_fc):
                arcpy.Delete_management(gap_fc)

            # ---------------- ROAD INTERSECTION ----------------
            road_A, road_B, road_C = [], [], []
            road_fc = None
            
            # Find matching line shapefile in the same directory
            for f in os.listdir(root_dir):
                if f.endswith("_Lines.shp"):
                    road_fc = os.path.join(root_dir, f)

            if road_fc and arcpy.Exists(road_fc):
                inter_fc = "in_memory\\road_inter"
                
                # Verify ROAD_TYPE exists to prevent crashes
                line_fields = [f.name for f in arcpy.ListFields(road_fc)]
                if "ROAD_TYPE" in line_fields:
                    arcpy.Intersect_analysis([fc, road_fc], inter_fc)

                    poly_fields = [f.name for f in arcpy.ListFields(fc)]
                    text_field = next((f for f in poly_fields if f.lower().startswith("text")), None)

                    if text_field:
                        with arcpy.da.SearchCursor(inter_fc, [text_field, "ROAD_TYPE"]) as cursor:
                            for row in cursor:
                                txt = str(row[0])
                                rtype = row[1]

                                if rtype == "A":
                                    road_A.append(txt)
                                elif rtype == "B":
                                    road_B.append(txt)
                                elif rtype == "C":
                                    road_C.append(txt)

            # remove duplicates
            road_A_str = ",".join(list(set(road_A))) if road_A else "-"
            road_B_str = ",".join(list(set(road_B))) if road_B else "-"
            road_C_str = ",".join(list(set(road_C))) if road_C else "-"

            # ---------------- FINAL ----------------
            total = blank_count + overlap_count + gap_count
            topo_status = "Done" if total == 0 else "Error"

            final_rows.append([
                lgd, name, blank_count, overlap_count, gap_count, total,
                topo_status, road_A_str, road_B_str, road_C_str
            ])
            
            # Clear in_memory workspace for the next iteration
            arcpy.Delete_management("in_memory")

# -------------------------------
# SAVE CSV
# -------------------------------
with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    header = [
        "LGD_CODE", "Village Name", "Blank Polygon", "Overlap", "Gap",
        "Count", "Topology", "ROAD_A", "ROAD_B", "ROAD_C"
    ]
    writer.writerow(header)
    writer.writerows(final_rows)

print("\n🔥 FINAL TOPOLOGY + ROAD QC DONE:", csv_path)
