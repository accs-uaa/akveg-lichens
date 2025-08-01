# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Create Table of Contents
# Author: Amanda Droghini
# Last Updated: 2025-07-29
# Usage: Execute in Python 3.13+.
# Description: "Create Table of Contents" creates a folder and Markdown file for each taxonomic group. The
# script formats taxonomic group names, creates folders and Markdown files, and adds front matter to the Markdown
# files for compatibility with Hugo. The script also exports a dataframe that links the taxon's original folder name
# with its processed folder name for use in subsequent scripts.
# ---------------------------------------------------------------------------

# Import required libraries
from pathlib import Path
import polars as pl
import textwrap
from utils import generate_taxon_name

# Set root directory
drive = Path('C:/')
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = drive / root_folder / 'Projects' / 'Lichen_Guide'
website_folder = drive / root_folder / 'Servers_Websites' / 'akveg-lichens'
output_folder = project_folder / 'outputs'

# Define input file
hierarchy_input = project_folder / 'Guide Master Folder_V_7_16_25' / 'Guide_Master_Reference_7_13_25.xlsx'

# Define output file
output_csv = output_folder / 'taxon_hierarchy.csv'

# Read input file
hierarchy = (pl.read_excel(hierarchy_input, columns=['Organization (variable)',
                                                  'Taxa Folder Name'])
             .rename({'Organization (variable)': "taxon_grouping",
         "Taxa Folder Name": "original_folder"
         }))

# Format taxon folder name
## Strips whitespaces and enforces consistent spelling of taxonomic abbreviations
hierarchy = hierarchy.with_columns(
    pl.col("original_folder").map_elements(generate_taxon_name,
                                           return_dtype=pl.String)
    .alias(
        "original_folder")
)

# Correct grouping for Squamarina lentigera
hierarchy = hierarchy.with_columns(
    pl.when(pl.col("original_folder") == "Squamarina lentigera")
    .then(pl.lit("Lobed Crusts, Select Crusts, Minutely Fruticose Species"))
    .otherwise(pl.col('taxon_grouping'))
    .alias('title_name')
)

# Rename verbose groups
mapping = {"gray crustose Caliciaceae": "Caliciaceae",  ## Combine into single Caliciaceae group
           "yellow crustose Caliciaceae": "Caliciaceae",
           "[Non-Shrub or Hair-Like] Fruticose Parmelioids": "Non-Shrub or Hair-Like Fruticose Parmelioids",
           "P. aphthosa-leucophlebia complex & similar": "P. aphthosa-leucophlebia Complex & Similar",
           "Lobed-Crusts, Select Crusts, Minutely Fruticose Species": "Lobed Crusts, Select Crusts, "
                                                                      "Minutely Fruticose Species",}

hierarchy = hierarchy.with_columns(
    pl.col('title_name')
    .str.replace_many(mapping)
    .alias('title_name'))

# Create folder names
## Further simplify verbose groups
mapping = {"Mushroom-Forming Lichens & Basidiolichens": "Mushroom-Forming",
           "Lobed Crusts, Select Crusts, Minutely Fruticose Species": "Crusts & Fruticose",
           "Pseudocyphellaria & Parmostictina": "Pseudo & Parmo",
           "Non-Shrub or Hair-Like Fruticose Parmelioids": "Non-Shrub Hair",
           "P. aphthosa-leucophlebia Complex & Similar": "Pelaph Complex",}

hierarchy = hierarchy.with_columns(
    pl.col('title_name')
    .str.replace_many(mapping)
    .str.replace_all(" Lichens|\\.", "")
    .str.to_lowercase()
    .str.replace_all(r"\s|&|-", "_")
    .str.replace_all(r"_+", value="_")
    .alias('taxon_folder'))

# Remove duplicates
hierarchy = (hierarchy.unique(subset=['original_folder', "title_name", "taxon_folder"])
                             .select(['original_folder', "title_name", "taxon_folder"]))

# Extract unique folder names
hierarchy_folders = (hierarchy
               .unique(subset=['title_name', "taxon_folder"])
               .select(['title_name', "taxon_folder"]))

# Determine order of table of contents
## Start at 10 to avoid overlap with intro pages
## Random ordering for now - Need Preston's feedback
hierarchy_folders = hierarchy_folders.with_columns(
    (pl.int_range(10, pl.len() + 10)).alias("order")
)

# Create new folders and index files
for row in hierarchy_folders.iter_rows(named=True):
    taxon_folder = row['taxon_folder']
    folder_path = Path(website_folder / 'content' / 'pages' / 'taxa' / taxon_folder)
    index_path = Path(folder_path / '_index.md')
    index_title = row['title_name']
    index_weight = row['order']
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

# Export hierarchy df as CSV
hierarchy.write_csv(output_csv)
