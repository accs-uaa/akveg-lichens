# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Resize and Copy Images
# Author: Amanda Droghini
# Last Updated: 2025-07-29
# Usage: Execute in Python 3.13+.
# Description: "Resize and Copy Images" identifies subfolders that contain images, creates short codes to use as file
# names, resizes images not to exceed 1800px on the largest axis, and copies the resized images to the /static folder
# of the akveg-lichens Hugo website. The script also exports a CSV file with the taxon name and export paths of each
# thumbnail for use in subsequent scripts.
# ---------------------------------------------------------------------------

# Import required libraries
from pathlib import Path
import polars as pl
from utils import collect_img_info
from utils import create_image_thumbnail

# Set root directory
drive = Path('C:/')
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = drive / root_folder / 'Projects' / 'Lichen_Guide'
taxa_folder = project_folder / 'Guide Master Folder_V_7_16_25' / 'Taxa Folders'
website_folder = drive / root_folder / 'Servers_Websites' / 'akveg-lichens'

# Define output folders
thumbnail_folder = website_folder / 'static' / 'images' / 'taxa'
csv_folder = project_folder / 'outputs'

# Define output file
output_csv = csv_folder / 'thumbnail_files.csv'

# Define minimum and output image dimensions
MINIMUM_SIZE = 1800
OUTPUT_SIZE = (1800, 1800)

# List all image files in subdirectories of taxa_folder
## Append subfolder path, taxon name, and taxonomic short code
img_list = collect_img_info(taxa_folder)

# Convert to polars df
img_files = pl.DataFrame(img_list)

# Ensure there are no nulls or empty strings
print(img_files.filter((pl.col("short_code").is_null()) | (pl.col('short_code')=='')).shape[0])

# Sequentially number images that belong to the same taxon
img_files = img_files.with_columns(
    (pl.int_range(0, pl.len()).over("short_code") + 1).alias("sequence_number")
)

# Pad numbers under 10 with a leading zero
img_files = img_files.with_columns(
    pl.col("sequence_number")
    .cast(pl.String)
    .str.zfill(2)
    .alias("sequence_number")
)

# Generate file name: short_code + sequence_number
img_files = img_files.with_columns(
    pl.concat_str(
        [
            pl.col("short_code"),
            pl.col("sequence_number"),
            pl.col("image_ext")
        ]
    ).alias("output_name")
)

# Define output path
img_files = img_files.with_columns(
    pl.concat_str(
            str(thumbnail_folder) + pl.lit("\\\\") + pl.col("output_name"))
    .alias("thumbnail_path"))

# Resize and copy images
print("Starting image processing loop...")
for row in img_files.iter_rows(named=True):
    input_path = row["input_path"]
    output_path = row["thumbnail_path"]

    # Call the function for each image pair
    create_image_thumbnail(input_path, output_path, MINIMUM_SIZE, OUTPUT_SIZE)
print("Image processing loop finished.")

# Export as CSV
img_files.write_csv(output_csv)
