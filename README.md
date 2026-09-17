# Gat-Map-Automation
1. 01_folder_setup_and_data_push.py
Automates the creation of the required Pandan_Georeff folder structures for each village. It cleans up legacy Survey Maps folders and migrates shapefiles, scan images, and DWG files from source directories into structured 01_Scan Image, 03_Drawing, and 04_Shape subdirectories. Generates a CSV migration report.

2. 02_shp_to_json.py
Iterates through the structured shapefile directories and converts line and polygon .shp files into .geojson formats for web mapping or lightweight data transfer.

3. 03_rectify_automation.py
Calculates combined buffered extents using arcpy.Describe and applies undistorted center-scale rigid alignments to spatial data. Outputs LZW compressed TIFF images.

4. 04_pdf_map_generation.py
Calculates village extents dynamically to determine the optimal paper size (A0, A1, A2, A3) and scale constraint. Exports professional cadastral layouts to PDF formats in the 07_PDF Map directory.

5. 05_topology_road_qc.py
A UI-prompted script that scans polygon and line shapefiles to detect topological errors. It identifies blank geometries, polygon overlaps, and gaps using the in_memory workspace for high-speed geoprocessing. It also intersects road layers to extract specific road types (A, B, C) and generates a Topology_QC_Final.csv report.

6. 06_external_excel_qc.py
A UI-prompted script that validates shapefile attributes against a master external Excel sheet. It checks polygon TEXT fields for missing values and duplicates, validates ROAD_TYPE fields for invalid or NULL entries, matches the total counts against the Excel baseline (last_pin, pin_count), and outputs a QC_Final_Report.csv
