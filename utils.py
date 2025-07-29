# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# utils.py
# Author: Amanda Droghini
# Last Updated: 2025-07-29
# ---------------------------------------------------------------------------

"""
This module provides a collection of utility functions to support the processing of subfolders, docx files,
and images within the project.

Functions included:
1. generate_short_code: Create a concise code from a subfolder (taxon) name.
2. enforce_abbr_period: Ensures that subspecies (ssp.) and species (spp.) abbreviations end with a period.
3. generate_taxon_name: Extracts a consistently formatted name from a path-like object whose final path component
represents a taxonomic entity.
4. collect_docx_info: Lists all Word documents (excluding hidden temp files) in the taxa directory, along with the
taxon name, taxon short code, and folder path.
5. collect_img_info: Lists all image files in the taxa directory, along with the taxon name, taxon short code,
and folder path.
6. has_images: Verifies whether a folder contains an image file.
7. create_image_thumbnail: Creates a thumbnail of specified dimensions from a single image.
"""

import re
from pathlib import Path
import PIL
from PIL import Image, UnidentifiedImageError

IMAGE_EXT = {".jpg", ".jpeg", ".png"}
ABBR_PATTERN = r"(ssp|spp)(?!\.)(\s*)(.*)"
ABBR_REPLACEMENT = r"\1.\2\3"

# --- Function 1 ---
def generate_short_code(taxon_name: str) -> str:
    """
    Generates a short code from a taxon name.

    Args:
        taxon_name: The name of the taxon.

    Returns:
        A concise string.
    """

    processed_name = (re.sub(r"&|\.|-|_|(spp)|(ssp)", "", taxon_name)
                      .lower()) # Remove unwanted characters and
    # convert to lowercase
    parts = processed_name.split()  # Splits by whitespace, handles multiple whitespaces between words

    if not parts:
        return "Error"  # Handle empty string case

    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        return "_".join([part[:5] for part in parts])
    else:
        if len(parts) > 2 and parts[0] == parts[2]:
            parts = [parts[0], parts[1]] + parts[3:] # Delete duplicate genus name
        return "_".join([part[:5] for part in parts])

# --- Function 2 ---
def enforce_abbr_period(taxon_name: str) -> str:
    """
    Enforces period after subspecies (ssp.) and species (spp.) abbreviations

    Args:
        taxon_name: Name of taxon to be processed.

    Return:
        A string with each instance of 'ssp' or 'spp' ending with a period
    """
    if taxon_name is None:
        return None
    return re.sub(ABBR_PATTERN, ABBR_REPLACEMENT, taxon_name)


# --- Function 3 ---
def generate_taxon_name(subfolder_path) -> str:
    """
    Extracts taxon name from a path-like object, removing trailing/leading underscores and whitespaces and calling
    enforce_abbr_period to enforce periods after 'ssp' and 'spp' abbreviations.

    Args:
        subfolder_path: The Path object for the directory that is named a taxon.

    Return:
        A processed string.
    """
    if subfolder_path is None:
        print("Warning: Input is None. Returning None.")
        return None

    if not isinstance(subfolder_path, Path):
        try:
            subfolder_path = Path(subfolder_path)
        except TypeError:  # Catch cases where input is not a string or Path (e.g., int, list)
            print(f"Error: Input '{subfolder_path}' is not a Path object or a string. Returning None.")
            return None
        except Exception as e:  # Catch any other potential errors during Path conversion
            print(f"Error: Could not convert '{subfolder_path}' to Path object. Details: {e}. Returning None.")
            return None

    taxon_name = str(subfolder_path.name).strip("_").strip()
    taxon_name = enforce_abbr_period(taxon_name)
    return taxon_name


# --- Function 4 ---
def collect_docx_info(taxa_folder: Path) -> list[dict]:
    """
    Collects information about DOCX files within a folder structure consisting of multiple subfolders (1 for each
    taxon).

    Args:
        taxa_folder: The Path object for the parent directory that contains the taxon subfolders.

    Returns:
        A list of dictionaries, where each dictionary contains information
        about a DOCX file.
    """
    docx_list = []  # Create empty list for storing file paths and taxa names

    for subfolder in taxa_folder.iterdir():
        if not (subfolder.is_dir() and subfolder.name.startswith('_')):
            continue

        # Check for docx files within the subfolder. If none, skip.
        # This prevents unnecessary processing of taxon_name and short_code.
        has_docx_files = any(True for _ in subfolder.rglob('*.docx'))
        if not has_docx_files:
            continue

        taxon_name = generate_taxon_name(subfolder)
        short_code = generate_short_code(taxon_name)

        for docx_file in subfolder.rglob('*.docx'):
            if not docx_file.name.startswith('~$'):  # Exclude temporary Word files
                docx_list.append({
                    "folder_path": str(subfolder),
                    "input_docx": str(docx_file),
                    "taxon_name": taxon_name,
                    "short_code": short_code,
                })
    return docx_list


# --- Function 5 ---
def collect_img_info(taxa_folder: Path) -> list[dict]:
    """
    Collects information about image files within a folder structure consisting of multiple subfolders (1 for each
    taxon).

    Args:
        taxa_folder: The Path object for the parent directory that contains the taxon subfolders.

    Returns:
        A list of dictionaries, where each dictionary contains information
        about an image file.
    """
    img_list = []  # Create empty list for storing file paths and taxa names

    for subfolder in taxa_folder.iterdir():
        if not(subfolder.is_dir() and subfolder.name.startswith('_')):
            continue

        if not has_images(subfolder):
            continue

        taxon_name = generate_taxon_name(subfolder)
        short_code = generate_short_code(taxon_name)

        for image_path in subfolder.rglob("*"):  # Use rglob for recursive search: Include sub-directories
            if image_path.is_file() and image_path.suffix.lower() in IMAGE_EXT:
                img_string = str(image_path)
                img_list.append({"folder_path": str(subfolder),
                                 "taxon_name": taxon_name,
                                 "short_code": short_code,
                                 "input_path": img_string,
                                 "image_ext": image_path.suffix.lower()
            })

    return img_list


# --- Function 6 ---
def has_images(taxa_folder: Path) -> bool:
    """
    Checks whether a folder contains 1+ image files.

    Args:
        taxa_folder: The Path object for the taxa directory.

    Returns:
        A Boolean where True indicates that the folder contains at least one image file.
    """
    for ext in IMAGE_EXT:
        if next(taxa_folder.rglob(f"*{ext}"), None) is not None:
            return True
    return False


# --- Function 7 ---
def create_image_thumbnail(input_path: Path, output_path: Path, minimum_size: int, output_size: tuple):
    """
    Processes a single image, resizing it as a thumbnail if its dimensions
    are not below a specified minimum size. The original image is not altered.

    Args:
        input_path: The source path for the image to be processed.
        output_path: The desired save path for the thumbnail.
        minimum_size: The minimum dimension (width or height) an image must have to be considered for resizing.
        Images with both dimensions smaller than this value will not be resized. This argument prevents images from
        being scaled larger than its original dimensions.
        output_size: A tuple (width, height) specifying the maximum dimensions for the thumbnail. The image will be
        resized while maintaining its aspect ratio, such that the largest dimension is no greater than the
        corresponding dimension in output_size.

    Returns:
        None: The function performs file operations and prints messages if errors are encountered, but does not return
        any value.
    """
    try:
        with Image.open(input_path) as img:
            if (img.width < minimum_size) and (img.height < minimum_size):
                print(f"{input_path} was not resized: Dimensions smaller than {minimum_size}.")
            else:
                img.thumbnail(output_size)
                img.save(output_path)
    except FileNotFoundError:
        print(f"Error: Source file not found at {input_path}")
    except PIL.UnidentifiedImageError:
        print(f"Error: File {input_path} is not a valid image file")
    except Exception as e:
        print(f"An error occurred while processing {input_path}: {e}")


# --- Example Usage ---
if __name__ == "__main__":
    print("--- Running examples for utils.py ---")

    # Test generate_short_code
    name1 = "_ Parmelia pseudosulcata "
    code1 = generate_short_code(name1)
    print(f"Short code for '{name1}': {code1}")

    name2 = "_Alectoria sarmentosa ssp vexillifera"  # Taxon with subspecies ('ssp') designation, missing a period
    new_name2 = enforce_abbr_period(name2)
    code2 = generate_short_code(name2)
    print(f"Short code for '{name2}': {code2}")
    print(f"New taxon name for '{name2}': {new_name2}")

    name3 = "_Calicium tigillare & Calicium pinicola"  # Two taxa with the same genus
    code3 = generate_short_code(name3)
    print(f"Short code for '{name3}': {code3}")

    name4 = "_Acolium inquinans & Pseudothelomma occidentale"  # Two taxa with different genera
    code4 = generate_short_code(name4)
    print(f"Short code for '{name4}': {code4}")

    name5 = "Stereocaulon spp"  # No period after 'spp'
    new_name5 = enforce_abbr_period(name5)
    code5 = generate_short_code(name5)
    print(f"Short code for '{name5}': {code5}")
    print(f"New taxon name for '{name5}': {new_name5}")

    name6 = "Alectoria sarmentosa ssp. sarmentosa"  # Subspecies with period after abbreviation
    new_name6 = enforce_abbr_period(name6)
    code6 = generate_short_code(name6)
    print(f"Short code for '{name6}': {code6}")
    print(f"New taxon name for '{name6}': {new_name6}")
