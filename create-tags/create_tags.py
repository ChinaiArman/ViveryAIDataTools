"""
"""

# PACKAGE IMPORTS
import openai
import argparse, os, shutil
import pandas as pd
import time
import re

# LOCAL FILE IMPORTS


# AI CONSTANTS
from keys import PRIMARY_CONTACT_KEY as OAI_API

# MISC CONSTANTS
LOCATION_COLUMNS = ["Location Name", "Location Headline", "Location Overview", "Location Announcements", "Location Action Links", "Location Tags", "Organization Name", "Organization About Us", "Organization Tags"]
PROGRAM_COLUMNS = ["Program Name", "Program Announcements", "Program Overview", "Food Program Category", "Location Name", "Location Headline", "Location Overview", "Location Announcements", "Location Action Links", "Location Tags"]




# HELPERS
def create_id_rows_dict(df: pd.DataFrame, primary_key: str, columns: list) -> dict:
    """
    """
    id_row_dict = {}
    for _, row in df.iterrows():
        row = row.fillna("NA")
        id_row_dict[row[primary_key]] = ", ".join(list(row[columns]))
    return id_row_dict


def generate_location_tags(id_locations_dict: dict) -> dict:
    """
    """
    pass


def generate_program_tags(id_programs_dict: dict) -> dict:
    """
    """
    pass


# TESTS




# MAIN
if __name__ == "__main__":
    # Define console parser
    parser = argparse.ArgumentParser(description="Identify the primary contacts from a bulk upload file")
    # Add file argument
    parser.add_argument("file", action="store", help="A bulk upload file")
    # Console arguments
    args = parser.parse_args()

    # Create DataFrame from file
    df = pd.read_csv(args.file)
    # Move CSV
    shutil.move(args.file, "datafiles/" + args.file.replace("datafiles\\", ""))
    # Create ID Rows Dictionary
    id_locations_dict = create_id_rows_dict(df, "Location External ID", LOCATION_COLUMNS)
    id_programs_dict = create_id_rows_dict(df, "Program External ID", PROGRAM_COLUMNS)
    
    # Parse Contacts through OAI
    print("Calling OpenAI Fine-Tuned Model...")
    location_tags_dict = generate_location_tags(id_locations_dict)
    program_tags_dict = generate_program_tags(id_programs_dict)