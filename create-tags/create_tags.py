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
PROGRAM_COLUMNS = ["Program Name", "Program Announcements", "Program Overview", "Program Service Category", "Food Program Category", "Location Name", "Location Headline", "Location Overview", "Location Announcements", "Location Action Links", "Location Tags"]
LOCATION_PROMPTS = {
"Languages Spoken":
"""
Given the following information, please determine what languages are spoken at this location. After the location, append the stop character '%%' to the end of the response. 

Input:
"Location Name: 'Famous Food Pantry', Location Headline: 'NA', Location Overview: 'NA', Location Announcements: 'NA', Location Action Links: 'NA', Location Tags: 'NA', Organization Name: 'Famous Food Network', Organization About Us: 'We make the best food', Organization Tags: 'NA'"
Output:
English%%
Input:
"Location Name: 'Refugio', Location Headline: 'Refugio anónimo', Location Overview: 'NA', Location Announcements: 'NA', Location Action Links: 'NA', Location Tags: 'NA', Organization Name: 'Refugios para todos', Organization About Us: 'NA', Organization Tags: 'NA'"
Output:
Spanish%%
"""
}
PROGRAM_PROMPTS = {

}




# HELPERS
def create_id_rows_dict(df: pd.DataFrame, primary_key: str, columns: list) -> dict:
    """
    """
    id_row_dict = {}
    for _, row in df.iterrows():
        row = row.fillna("NA")
        row = row.str.replace(",", "")
        row = row.apply(str)
        row.to_csv("test.csv")
        id_row_dict[row[primary_key]] = ", ".join(list(row[columns]))
    return id_row_dict


def call_oai(prompt: str, case: str) -> str:
    """
    """
    openai.api_type = "azure"
    openai.api_base = OAI_API["base"]
    openai.api_version = "2023-09-15-preview"
    openai.api_key = OAI_API["key"]
    response = openai.Completion.create(
        engine=OAI_API["engine"],
        prompt=f'{prompt}\nInput: "{case}"\nOutput: ',
        temperature=0.4,
        max_tokens=100,
        top_p=0.25,
        frequency_penalty=0,
        presence_penalty=0,
        best_of=2,
        stop=["%%"]
    )
    time.sleep(0.05)
    print(response["choices"][0]["text"].strip())
    return response["choices"][0]["text"].strip()


def generate_location_tags(id_locations_dict: dict) -> dict:
    """
    """
    location_tags_dict = {}
    for locationID, case in id_locations_dict.items():
        location_tags_dict[locationID] = {}
        for prompt_name, prompt in LOCATION_PROMPTS.items():
            case = case.split(", ")
            case = ", ".join([LOCATION_COLUMNS[i] + ": '" + case[i] + "'" for i in range(len(case))])
            response = call_oai(prompt, case)
            location_tags_dict[locationID][prompt_name] = response
    return location_tags_dict


def generate_program_tags(id_programs_dict: dict) -> dict:
    """
    """
    program_tags_dict = {}
    for programID, case in id_programs_dict.items():
        program_tags_dict[programID] = {}
        for prompt_name, prompt in PROGRAM_PROMPTS.items():
            response = call_oai(PROGRAM_PROMPTS[prompt], case)
            program_tags_dict[programID][prompt_name] = response
    return program_tags_dict


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
    if '.xlsx' in args.file:
        df = pd.read_excel(args.file)
    else:
        df = pd.read_csv(args.file)
    
    # Create CSVs Directory
    if not os.path.isdir('datafiles'):
        os.mkdir('datafiles')
    # Move CSV
    shutil.move(args.file, "datafiles/" + args.file.replace("datafiles\\", ""))
    # Create ID Rows Dictionary
    id_locations_dict = create_id_rows_dict(df, "Location External ID", LOCATION_COLUMNS)
    print(id_locations_dict)
    id_programs_dict = create_id_rows_dict(df, "Program External ID", PROGRAM_COLUMNS)
    
    # Parse Contacts through OAI
    print("Calling OpenAI Fine-Tuned Model...")
    location_tags_dict = generate_location_tags(id_locations_dict)
    print(location_tags_dict)
    # program_tags_dict = generate_program_tags(id_programs_dict)