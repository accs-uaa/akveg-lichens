# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Create Table of Contents
# Author: Amanda Droghini
# Last Updated: 2025-07-22
# Usage: Execute in Python 3.13+.
# Description: "Create Table of Contents" creates a website folder and index file for each taxonomic group. The
# script formats group names and adds front matter to the index Markdown file for compatibility with the static website
# generator Hugo.
# ---------------------------------------------------------------------------

# Import required libraries
from pathlib import Path
import polars as pl
import textwrap

# Set root directory
drive = Path('C:/')
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = drive / root_folder / 'Projects' / 'Lichen_Guide' / 'Guide Master Folder_V_7_16_25'
website_folder = drive / root_folder / 'Servers_Websites' / 'akveg-lichens'

# Define input files
taxa_org_input = project_folder / 'Guide_Master_Reference_7_13_25.xlsx'

# Read input file
taxa_org = pl.read_excel(taxa_org_input, columns=['Organization (variable)',
                                                  'Taxa Folder Name'])

# Correct group for Squamarina lentigera
taxa_org = taxa_org.with_columns(
    pl.when(pl.col("Taxa Folder Name") == "Squamarina lentigera")
    .then(pl.lit("Lobed Crusts, Select Crusts, Minutely Fruticose Species"))
    .otherwise(pl.col('Organization (variable)'))
    .alias('title_name')
)

# Rename verbose groups
mapping = {"gray crustose Caliciaceae": "Caliciaceae",  ## Combine into single Caliciaceae group
           "yellow crustose Caliciaceae": "Caliciaceae",
           "[Non-Shrub or Hair-Like] Fruticose Parmelioids": "Non-Shrub or Hair-Like Fruticose Parmelioids",
           "P. aphthosa-leucophlebia complex & similar": "P. aphthosa-leucophlebia Complex & Similar",
           "Lobed-Crusts, Select Crusts, Minutely Fruticose Species": "Lobed Crusts, Select Crusts, "
                                                                      "Minutely Fruticose Species",
           " spp.": ""}

taxa_org = taxa_org.with_columns(
    pl.col('title_name')
    .str.replace_many(mapping)
    .alias('title_name'))

# Create folder names
## Further simplify of verbose groups
mapping = {"Mushroom-Forming Lichens & Basidiolichens": "Mushroom-Forming",
           "Lobed Crusts, Select Crusts, Minutely Fruticose Species": "Crusts & Fruticose",
           "Pseudocyphellaria & Parmostictina": "Pseudo & Parmo",
           "Non-Shrub or Hair-Like Fruticose Parmelioids": "Non-Shrub Hair",
           "P. aphthosa-leucophlebia Complex & Similar": "Pelaph Complex",
           " Genera": ""}

taxa_org = taxa_org.with_columns(
    pl.col('title_name')
    .str.replace_many(mapping)
    .str.replace_all(" Lichens", "")
    .str.to_lowercase()
    # .str.replace_many(["likes"], ["like"])
    .str.replace_all(r"\s|&|-", "_")
    .str.replace_all(r"_+", value="_")
    .alias('folder_name'))

# Extract unique folder names
org_folders = (taxa_org
               .unique(subset=['title_name', "folder_name"])
               .select(['title_name', "folder_name"]))

# Determine order of table of contents
## Start at 10 to avoid overlap with intro pages
## Random ordering for now - Need Preston's feedback
org_folders = org_folders.with_columns(
    (pl.int_range(10, pl.len() + 10)).alias("order")
)

# Create new folders and index files
for new_folder in org_folders['folder_name']:
    folder_path = Path(website_folder / 'content' / 'pages' / 'taxa' / new_folder)
    index_path = Path(folder_path / '_index.md')
    index_title = org_folders.filter(pl.col('folder_name') == new_folder)['title_name'].item()
    index_weight = org_folders.filter(pl.col('folder_name') == new_folder)['order'].item()
    Path.mkdir(folder_path, parents=True, exist_ok=True)

    with (open(index_path, 'w', encoding='utf-8') as index_file):
        # Write front matter
        front_matter = textwrap.dedent(f"""\
        ---
        title: "{index_title}"
        type: docs
        weight: {index_weight}
        bookFlatSection: true
        bookCollapseSection: true
        ---
        
        
        """)

        index_file.write(front_matter)
