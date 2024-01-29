"""
Clean Hours Script

@author Arman Chinai
@version 1.0.1
"""

# PACKAGE IMPORTS
import openai
import argparse, os, shutil
import pandas as pd

# LOCAL FILE IMPORTS


# AI CONSTANTS
from keys import CLEAN_HOURS_KEY as OAI_API

# MISC CONSTANTS
PROMPT = """"""




# HELPERS
def list_of_strings(arg: str) -> list:
    """
    """
    return arg.split(',')


def create_id_contacts_dict(df: pd.DataFrame, primary_key: str, contact_columns: list) -> dict:
    """
    """
    id_hours_dict = {}
    for _, row in df.iterrows():
        id_hours_dict[row[primary_key]] = ", ".join(row[contact_columns].tolist()).strip()
    return id_hours_dict




# TESTS




# MAIN
if __name__ == '__main__':
    # Define console parser
    parser = argparse.ArgumentParser(description="Identify the primary contacts from a bulk upload file")
    # Add file argument
    parser.add_argument("file", action="store", help="A bulk upload file")
    # Add primary key argument
    parser.add_argument("primary_key", action="store", help="A unique key to identify each row")
    # Add column arguments
    parser.add_argument("--columns", type=list_of_strings, action="store", help="The columns that contain contact information")
    # Console arguments
    args = parser.parse_args()

    # Create DataFrame
    df = pd.read_csv(args.file)
    # Move CSV
    # shutil.move(args.file, "csvs/" + args.file.replace("csvs\\", ""))
    # Create id_hours Dictionary
    id_hours_dict = create_id_contacts_dict(df, args.primary_key, args.columns)
    # Create is_valid_hours Dictionary
    is_valid_hours_dict = {key: True for key, _ in id_hours_dict.items()}
