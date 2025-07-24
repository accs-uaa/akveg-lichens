# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Resize and Copy Images
# Author: Amanda Droghini
# Last Updated: 2025-07-23
# Usage: Execute in Python 3.13+.
# Description: "Resize and Copy Images" identifies subfolders that contain images, creates short codes to use as file
# names, resizes images not to exceed 1800px on the largest axis, and copies the resized images to the /static folder
# of the akveg-lichens Hugo website.
# ---------------------------------------------------------------------------

# Import required libraries
from pathlib import Path
import re
import polars as pl
from PIL import Image

# Set root directory
drive = Path('C:/')
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = drive / root_folder / 'Projects' / 'Lichen_Guide'
taxa_folder = project_folder / 'Guide Master Folder_V_7_16_25' / 'Taxa Folders'
website_folder = drive / root_folder / 'Servers_Websites' / 'akveg-lichens'

# Define output folder
output_folder = website_folder / 'static' / 'images' / 'taxa'

# Define function to check whether a folder contains one or more images
def has_images(folder_path: Path) -> bool:
    image_extensions = {".jpg", ".jpeg", ".png"}
    for ext in image_extensions:
        if next(folder_path.rglob(f"*{ext}"), None) is not None:
            return True
    return False

# Define minimum and output image dimensions
minimum_size = 1800
output_size = (1800, 1800)

# Create empty list for storing image file paths
img_list = []

# Iterate across directories that have images
## Exclude folders that do not start with a '_' (indicates in-progress taxa)
## Create shorthand names and obtain image file paths
for subfolder in taxa_folder.iterdir():
    if subfolder.is_dir() and subfolder.name.startswith('_'):
        if has_images(subfolder):
            subfolder_string = str(subfolder)
            taxon_name = subfolder.name.strip("_").strip()
            # Create short code depending on length of string
            short_code = re.sub(r"&\s|\.|-|(spp)|(ssp)", "", taxon_name).lower()
            short_code = short_code.split()
            if len(short_code)==1:
                short_code = short_code[0]
            elif len(short_code)==2:
                short_code = "_".join([part[:5] for part in short_code])
            elif len(short_code)>2 and short_code[0] == short_code[2]:
                del (short_code[2])
                short_code = "_".join([part[:5] for part in short_code])
            else:
                short_code = "_".join([part[:5] for part in short_code])

            # Obtain image path and append to image list
            image_extensions = {".jpg", ".jpeg", ".png"}
            for ext in image_extensions:
                for image_path in subfolder.rglob(f"*{ext}"):
                    img_string = str(image_path)
                    img_list.append({"folder_path": subfolder_string,
                                 "taxon_name": taxon_name,
                                 "short_code": short_code,
                                 "input_path": img_string,
                                 "image_ext": image_path.suffix})
        else:
            print(f"'{subfolder.name}': No images found.")

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
            str(output_folder) + pl.lit("\\\\") + pl.col("output_name"))
    .alias("output_path"))

# Resize and copy images
for new_path in img_files['output_path']:
    src_path = Path(img_files.filter(pl.col('output_path') == new_path)['input_path'].item())
    with Image.open(src_path) as im:
        if (im.width < minimum_size) and (im.height < minimum_size):
            print(f"{src_path} was not resized; dimension too small.")
        else:
            im.thumbnail(output_size)
            im.save(new_path)
