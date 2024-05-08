"""
"""

# PACKAGE IMPORTS
import openai
import argparse, os, shutil
import pandas as pd
import time
from langcodes import Language
from langdetect import detect_langs
import re

# LOCAL FILE IMPORTS


# AI CONSTANTS
from keys import TAGS_KEY as OAI_API

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
""",
"Location Features":
"""
Given the following information, please determine what location features from the list below could be available at this location.
!!! ONLY USE THE FEATURES LISTED BELOW !!!.
After the feature, append the stop character '%%' to the end of the response.
 
Feature List:
    - Air Conditioning
    - Near Public Transit
    - Parking Available
    - Restroom Available
    - Safe Space
    - Seating in Waiting Area
    - Wheelchair Accessible
    - WiFi Available
 
Input: "Location Name: 'Famous Food Pantry', Location Headline: 'NA', Location Overview: 'Free Wifi and Public Washrooms', Location Announcements: 'NA', Location Action Links: 'NA', Location Tags: 'NA', Organization Name: 'Famous Food Network', Organization About Us: 'We make the best food', Organization Tags: 'NA'"
Output: WiFi Available/Restroom Available%%
 
Input: "Location Name: 'Refugio', Location Headline: 'Refugio anónimo', Location Overview: 'ramp access', Location Announcements: 'NA', Location Action Links: 'NA', Location Tags: 'NA', Organization Name: 'Refugios para todos', Organization About Us: 'Providing shelter in both english and spanish.', Organization Tags: 'NA'"
Output: Wheelchair Accessible%%
 
Input: "Location Name: 'Pantry', Location Headline: 'NA', Location Overview: 'We provide food access to impoverished communities.', Location Announcements: 'NA', Location Action Links: 'NA', Location Tags: 'NA', Organization Name: 'Pantry Network', Organization About Us: 'NA', Organization Tags: 'NA'"
Output: NA%%
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
        id = row[primary_key]
        row = row.str.replace(",", "")
        row = row.apply(str)
        id_row_dict[id] = ", ".join(list(row[columns]))
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
            location_tags_dict[locationID][prompt_name + ' [A]'] = response
    return location_tags_dict


def generate_program_tags(id_programs_dict: dict) -> dict:
    """
    """
    program_tags_dict = {}
    for programID, case in id_programs_dict.items():
        program_tags_dict[programID] = {}
        for prompt_name, prompt in PROGRAM_PROMPTS.items():
            response = call_oai(PROGRAM_PROMPTS[prompt], case)
            program_tags_dict[programID][prompt_name + ' [A]'] = response
    return program_tags_dict




# TESTS
def language_check(id_locations_dict: dict, location_tags_dict) -> dict:
    """
    """
    for location_id, value in id_locations_dict.items():
        value = value.replace("NA", "")
        location_languages = detect_langs(value)
        location_languages = [str(lang).split(":")[0] for lang in location_languages]
        location_languages = [Language.make(language=language).display_name() for language in location_languages]
        location_tags_dict[location_id]['Languages Spoken [T]'] = " ,".join(location_languages)
    return location_tags_dict


def feature_check(features: list, id_locations_dict: dict, location_tags_dict: dict) -> dict:
    """
    """
    for location_id, value in id_locations_dict.items():
        features_detected = []
        for feature in features:
            if feature in value:
                features_detected.append(feature)
            location_tags_dict[location_id]['Location Features [T]'] = " ,".join(features_detected)
    return location_tags_dict




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

    # Check responses
    language_check(id_locations_dict, location_tags_dict)
    print(location_tags_dict)
    # program_tags_dict = generate_program_tags(id_programs_dict)