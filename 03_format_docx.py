# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Format Taxa Descriptions
# Author: Amanda Droghini
# Last Updated: 2025-07-29
# Usage: Execute in Python 3.13+.
# Description: "Format Taxa Descriptions" reads in Word documents, separates section headings from text, re-formats
# the document using Markdown, and adds Hugo front matter. The output is a Markdown file that can be converted to a
# HTML page using the static website generator Hugo.
# ---------------------------------------------------------------------------

# Import required libraries
from pathlib import Path
import re
import textwrap
from docx import Document
import polars as pl
from utils import collect_docx_info

# Set root directory
drive = Path('C:/')
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = drive / root_folder / 'Projects' / 'Lichen_Guide'
taxa_folder = project_folder / 'Guide Master Folder_V_7_16_25' / 'Taxa Folders'
website_folder = drive / root_folder / 'Servers_Websites' / 'akveg-lichens'

# Define output folder
output_folder = website_folder / 'content' / 'taxa'

# Define input files
hierarchy_input = project_folder / 'outputs' / 'taxon_hierarchy.csv'

# Read in input file
hierarchy = pl.read_csv(hierarchy_input)

# Identify all .docx files in subdirectories of taxa_folder
docx_list = collect_docx_info(taxa_folder)

# Convert to polars df
docx_files = pl.DataFrame(docx_list)

# Obtain name of output folder based on taxon organization

## Remove periods to match formatting in hierarchy CSV -- PROBABLY NO LONGER NEEDED
docx_files = docx_files.with_columns(
    pl.col("taxon_name").
    str.replace_all("\\.", value="")
    .alias("join_name")
)

## Join dataframes on taxon_name
docx_hierarchy = docx_files.join(hierarchy, left_on='join_name', right_on='original_folder', how='left')

## Replace non-matches (null values) with group name
docx_hierarchy = docx_hierarchy.with_columns(
    pl.when((pl.col("taxon_folder").is_null()) & pl.col('join_name').str.contains("Cladonia"))
    .then(pl.lit("cladoniaceae"))
    .when((pl.col("taxon_folder").is_null()) & pl.col('join_name').str.contains("Thamnolia|Siphula|Lepra"))
    .then(pl.lit("icmadophilaceae"))
    .when((pl.col("taxon_folder").is_null()) & pl.col('join_name').str.contains("Dactylina|Allocetraria"))
    .then(pl.lit("non_shrub_hair"))
    .when(pl.col("taxon_folder").is_null())
    .then(pl.col("join_name"))
    .otherwise(pl.col("taxon_folder"))
    .alias("taxon_folder")
)

## Replace remaining missing matches
text_mapping = {"Glypholecia scabra":"scales_squamule_like",
                "Lobaria linita & Lobaria tenuior": "lungworts",
                "Rusavskia elegans & Rusavskia sorediata": "teloschistaceae",
                "Sporastatia polyspora & Sporastatia testudinea": "crusts_fruticose","Xanthoparmelia spp": "shield_like_parmelioids",
}

docx_hierarchy = docx_hierarchy.with_columns(
    pl.col("taxon_folder").replace(text_mapping)  # Keeps original value if not listed in dictionary
    .alias("taxon_folder")
)

## Ensure that all null values have been addressed
print(docx_hierarchy['taxon_folder'].is_null().sum())

# Define output paths based on taxon organization
docx_hierarchy = (docx_hierarchy.with_columns(
    pl.concat_str(str(output_folder) +
                  pl.lit("\\") +
                  pl.col("taxon_folder") +
                  pl.lit("\\") +
                  pl.col("short_code") +
                  pl.lit(".md"))
    .alias('output_path')
)
                  .select(['taxon_name', 'input_docx', 'output_path']))

# Process taxonomic description into Markdown file

# Generate temp to test
temp = docx_hierarchy[0:3]

for row in temp.iter_rows(named=True):
    docx_path = row['input_docx']  # Keep as string
    md_path = Path(row['output_path'])
    taxon_name = row['taxon_name']

    # Open Word document
    document = Document(docx_path)

    with (open(md_path, 'w', encoding='utf-8') as md_file):
        print(f"Writing Markdown to {md_path}...")

        # Write front matter
        front_matter = textwrap.dedent(f"""\
        title: "{taxon}"
        type: docs
        ---


        """)

        md_file.write(front_matter)

        # Write Heading 1

        md_file.write("# " + taxon + "\n\n")

        ###### Insert first image - NEED TO CODE
        md_file.write("![" + taxon + "](/images/file_name.jpg)")

        # Format subsequent headings + paragraph text

        for para in document.paragraphs:
            split_para = re.split(pattern=r':\s(.*)', string=para.text, maxsplit=2)
            if len(split_para) > 1:
                para_heading = split_para[0].strip()
                para_text = split_para[1].strip()
                # Format heading
                formatted_heading = "## " + para_heading
                # Concatenate heading and paragraph text
                formatted_line = formatted_heading + "\n" + para_text + "\n\n"
                md_file.write(formatted_line)
            elif len(para.text) < 15:
                print(f"Skipping writing string", para.text)
            else:
                formatted_line = para.text + "\n\n"
                md_file.write(formatted_line)

        ##### Insert subsequent images (or all images?) under heading "Photos?"
