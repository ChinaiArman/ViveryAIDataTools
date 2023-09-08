"""
"""


# PACKAGE IMPORTS
import openai
import argparse, os, shutil
import pandas as pd

# LOCAL FILE IMPORTS


# IMPORT CONSTANTS
from keys import API_KEY

# MISC CONSTANTS





# HELPERS
def create_id_hours_dict(df: pd.DataFrame) -> dict:
    """
    """
    id_hours_dict = {}
    for _, row in df.iterrows():
        id_hours_dict[row["Program External ID"]] = str(row["Hours Uncleaned"]).strip()
    return id_hours_dict


def call_oai(prompt: str) -> str:
    """
    """
    openai.api_type = "azure"
    openai.api_base = "https://viveryadvocate.openai.azure.com/"
    openai.api_version = "2022-12-01"
    openai.api_key = API_KEY
    response = openai.Completion.create(
        engine="arman_hours_clean_model",
        prompt=f"Q: {prompt}\nA:",
        temperature=0.2,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        best_of=1,
        stop=["%%"]
    )
    return response["choices"][0]["text"]


def format_hours_iteratively(id_hours_dict: dict) -> dict:
    """
    """
    cleaned_hours_dict = {}
    for key, value in id_hours_dict.items():
        new_value = call_oai(value)
        new_value = new_value.replace("\n", "").replace("Q:", "").replace("A:", "").replace(value, "").strip()
        new_value = new_value
        cleaned_hours_dict[key] = new_value
    return cleaned_hours_dict


def test_hours_format(cleaned_hours_dict: dict, is_valid_hours_dict: dict) -> dict:
    """
    """
    return


def test_hours_contain_base_string(cleaned_hours_dict: dict, is_valid_hours_dict: dict) -> dict:
    """
    """
    return


def filter_invalid_values(id_hours_dict: dict, cleaned_hours_dict: dict, is_valid_hours_dict: dict) -> dict:
    """
    """
    valid_hours_dict = {}
    for key, _ in cleaned_hours_dict.items():
        if is_valid_hours_dict[key]:
            valid_hours_dict[key] = cleaned_hours_dict[key]
        else:
            valid_hours_dict[key] = id_hours_dict[key]
    return valid_hours_dict


def convert_id_hours_dict_to_df(cleaned_hours_dict: dict, is_valid_hours_dict: dict, df: pd.DataFrame) -> pd.DataFrame:
    """
    """
    return




# MAIN
if __name__ == "__main__":
    # Define console parser
    parser = argparse.ArgumentParser(description="Clean a bulk upload files hours")
    # Add file argument
    parser.add_argument("file", action="store", help="A bulk upload file")
    # Console arguments
    args = parser.parse_args()

    # Create directory name
    directory = "data_" + args.file.split("\\")[-1].replace(".csv", "")
    # Create DataFrame
    df = pd.read_csv(args.file)
    
    # Create directory within project folder
    # if not os.path.isdir(directory):
    #     os.mkdir(directory)
    # # Move file to directory
    # if args.file.split("\\")[0] != directory:
    #     shutil.move(args.file, directory)

    # Create id_hours Dictionary
    id_hours_dict = create_id_hours_dict(df)

    # Create is_valid_hours Dictionary
    is_valid_hours_dict = {key: True for key, _ in id_hours_dict.items()}

    # Parse Hours through OAI
    cleaned_hours_dict = format_hours_iteratively(id_hours_dict)

    # Test OAI Hours 
    is_valid_hours_dict = test_hours_format(cleaned_hours_dict, is_valid_hours_dict)
    is_valid_hours_dict = test_hours_contain_base_string(cleaned_hours_dict, is_valid_hours_dict)
    #

    # Check Values Still Valid
    valid_id_hours_dict = filter_invalid_values(id_hours_dict, cleaned_hours_dict, is_valid_hours_dict)

    # Convert Back to DF
    cleaned_hours_df = convert_id_hours_dict_to_df(cleaned_hours_dict, is_valid_hours_dict, df)