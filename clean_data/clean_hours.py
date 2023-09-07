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
def create_id_hours_dict(df:pd.DataFrame) -> dict:
    """
    """
    return


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
    return


def convert_id_hours_dict_to_df(id_hours_dict: dict, df: pd.DataFrame) -> pd.DataFrame:
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
    if not os.path.isdir(directory):
        os.mkdir(directory)
    # Move file to directory
    if args.file.split("\\")[0] != directory:
        shutil.move(args.file, directory)

    print(call_oai("Mon-Fri,10:00:00 AM,4:00:00 PM"))