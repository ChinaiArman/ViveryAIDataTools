"""
Primary Contacts Script

@author Arman Chinai
@version 1.0.1
"""

# PACKAGE IMPORTS
import openai
import argparse, os, shutil
import pandas as pd
import time
import itertools

# LOCAL FILE IMPORTS


# AI CONSTANTS
from keys import PRIMARY_CONTACT_KEY as OAI_API

# MISC CONSTANTS
EXTENSION_KEYWORDS = ["ext", "extension", "ext."]
PROMPTS = {
"Number": 
"""
Extract the phone from the following string, and append "%%" DIRECTLY after the number. 

!!! Format the number using the following format: "XXX-XXX-XXXX%%", with "X" representing a digit 0-9.
!!! If there is no phone number present in the following text, return "NA" followed by "%%"

Input: "(513)-153-5915, johnnyappleseed@gmail.com"
Output: 513-153-5915%%

Input: "John Cena, johncena@vivery.org, 603-654-4524"
Output: 603-654-4524%%
""",
"Email": 
"""
Extract the EMAIL ADDRESS from the following string, and append "%%" DIRECTLY after the email domain. 

!!! Format the email using the following format: "[prefix]@[domain].[extension]%%".
!!! If there is NO EMAIL PRESENT in the following text, return "NA" followed by "%%"

Input: "513-153-5915, johnnyappleseed@gmail.com"
Output: johnnyappleseed@gmail.com%%

Input: "John Cena, johncena@vivery.org, 603-654-4524"
Output: johncena@us.gov%%
""",
"Name": 
"""
Please tell me the first and last name of this person from the following string and and append "%%" DIRECTLY after the name.

!!! Do NOT use NUMBERS or SPECIAL CHARACTERS
!!! If there is NO NAME PRESENT in the following text, return "NA" followed by "%%"

Input: "Johnny Appleseed"
Output: Johnny Appleseed%%

Input: "John Cena, johncena@vivery.org, 603-654-4524"
Output: John Cena%%

Input: "735-0043-4014"
Output: NA%%
""",
"Extension": 
"""
Extract the phone extension from the following string, and append "%%" DIRECTLY after the number. 

!!! Format the extension using the following format: "XXXX%%", with "X" representing a digit 0-9. The number of digits depends on the length of the phone extension.
!!! If there is no extension present in the following text, return "NA" followed by "%%"
!!! DO NOT INCLUDE NUMBERS THAT ARE APART OF EMAIL ADDRESSES OR THE BASE PHONE NUMBER, ONLY NUMBERS CLEARLY MARKED AS EXTENSIONS.

Input: "513-153-5915 EXT 5315, johnnyappleseed19845@gmail.com"
Output: 5315%%

Input: "John Cena, johncena@vivery.org, 158-159-0915"
Output: NA%%
"""
}


# HELPERS
def list_of_strings(arg: str) -> list:
    """
    """
    return arg.split(',')


def create_id_contacts_dict(df: pd.DataFrame, primary_key: str, contact_columns: list) -> dict:
    """
    """
    id_contacts_dict = {}
    for _, row in df.iterrows():
        row = row.fillna("NA")
        id_contacts_dict[row[primary_key]] = ", ".join(list(row[contact_columns])).strip()
    return id_contacts_dict


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
        max_tokens=50,
        top_p=0.25,
        frequency_penalty=0,
        presence_penalty=0,
        best_of=2,
        stop=["%%"]
    )
    time.sleep(0.05)
    print("\tOAI API Response: " + response["choices"][0]["text"])
    return response["choices"][0]["text"].strip()


def format_contacts_iteratively(id_contacts_dict: dict) -> dict:
    """
    """
    primary_contacts_dict = {}
    for key, value in id_contacts_dict.items():
        primary_contacts_dict[key] = {prompt_type: call_oai(prompt, value) for prompt_type, prompt in PROMPTS.items()}
        primary_contacts_dict[key]["Errors"] = []
    return primary_contacts_dict


def filter_invalid_values(primary_contacts_dict: dict, is_valid_contact_dict: dict) -> dict:
    """
    """
    valid_contacts_dict = {}
    for key, _ in primary_contacts_dict.items():
        if is_valid_contact_dict[key]:
            valid_contacts_dict[key] = primary_contacts_dict[key]
        else:
            valid_contacts_dict[key] = [""] * 4           
    return valid_contacts_dict


def convert_id_hours_dict_to_df(valid_id_contacts_dict: dict, is_valid_contact_dict: dict) -> pd.DataFrame:
    """
    """
    pass




# TESTS
def test_name_in_original_string(id_contacts_dict: dict, primary_contacts_dict: dict, is_valid_contact_dict: dict) -> dict:
    """
    """
    for key, value in primary_contacts_dict.items():
        is_valid = True
        try:
            for name in value["Name"].split(" "):
                is_valid = (name.lower() in id_contacts_dict[key].lower() or name == "NA") and is_valid
        except: 
            pass
        
        if not is_valid:
            is_valid_contact_dict[key]["Name"] = max(1, is_valid_contact_dict[key]["Name"])
            primary_contacts_dict[key]["Errors"].append("WARNING: Name not found within original contact information.")

    return is_valid_contact_dict


def test_name_format(_: dict, primary_contacts_dict: dict, is_valid_contact_dict: dict) -> dict:
    """
    """
    for key, value in primary_contacts_dict.items():
        is_valid = True
        try:
            is_valid = value["Name"].replace(" ", "").isalpha() and is_valid
            for name in value["Name"].split(" "):
                is_valid = name[0].isupper() and is_valid
        except:
            if value["Name"] != "NA":
                is_valid = False

        if not is_valid:
            is_valid_contact_dict[key]["Name"] = max(2, is_valid_contact_dict[key]["Name"])
            primary_contacts_dict[key]["Errors"].append("ERROR: Name formatting is not valid (FirstName LastName).")

    return is_valid_contact_dict


def test_extension_in_original_string(id_contacts_dict: dict, primary_contacts_dict: dict, is_valid_contact_dict: dict) -> dict:
    """
    """
    for key, value in primary_contacts_dict.items():
        is_valid = True
        try:
            is_valid = (value["Extension"] in id_contacts_dict[key] or value["Extension"] == "NA") and is_valid
        except:
            pass

        if not is_valid:
            is_valid_contact_dict[key]["Extension"] = max(1, is_valid_contact_dict[key]["Extension"])
            primary_contacts_dict[key]["Errors"].append("WARNING: Extension not found within original contact information.")
        
    return is_valid_contact_dict


def test_extension_format(_: dict, primary_contacts_dict: dict, is_valid_contact_dict: dict) -> dict:
    """
    """
    for key, value in primary_contacts_dict.items():
        is_valid = True
        try:
            int(value["Extension"])
        except: 
            if value["Extension"] != "NA":
                is_valid = False

        if not is_valid:
            is_valid_contact_dict[key]["Extension"] = max(2, is_valid_contact_dict[key]["Extension"])
            primary_contacts_dict[key]["Errors"].append("ERROR: Extension is not numerical.")
        
    return is_valid_contact_dict


def test_extension_keyword_in_original_string(id_contacts_dict: dict, primary_contacts_dict: dict, is_valid_contact_dict: dict) -> dict:
    """
    """
    for key, value in id_contacts_dict.items():
        is_valid = False
        try:
            if primary_contacts_dict[key]["Extension"] == "NA":
                is_valid = True
            else:
                for extension in EXTENSION_KEYWORDS:
                    is_valid = extension in value.lower() or is_valid
        except:
            pass

        if not is_valid:
            is_valid_contact_dict[key]["Extension"] = max(1, is_valid_contact_dict[key]["Extension"])
            primary_contacts_dict[key]["Errors"].append("WARNING: Extension Keyword not found within original contact information.")
        
    return is_valid_contact_dict


def test_extension_found_within_phone_number(_: dict, primary_contacts_dict: dict, is_valid_contact_dict: dict) -> dict:
    """
    """
    for key, value in primary_contacts_dict.items():
        is_valid = True
        try:
            if value["Extension"] in value["Number"].replace("-", "") and value["Extension"] != "NA":
                is_valid = False
        except: 
            is_valid = True

        if not is_valid:
            is_valid_contact_dict[key]["Extension"] = max(1, is_valid_contact_dict[key]["Extension"])
            primary_contacts_dict[key]["Errors"].append("ERROR: Extension found within phone number.")
        
    return is_valid_contact_dict


def test_extension_present_without_phone_number(_: dict, primary_contacts_dict: dict, is_valid_contact_dict: dict) -> dict:
    """
    """
    for key, value in primary_contacts_dict.items():
        is_valid = True
        try:
            if value["Number"] == "NA":
                is_valid = value["Extension"] == "NA" and is_valid
        except: 
            is_valid = True

        if not is_valid:
            is_valid_contact_dict[key]["Extension"] = max(2, is_valid_contact_dict[key]["Extension"])
            primary_contacts_dict[key]["Errors"].append("ERROR: Extension present without phone number.")
        
    return is_valid_contact_dict




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
    if '.xlsx' in args.file:
        df = pd.read_excel(args.file)
    else:
        df = pd.read_csv(args.file)
    # Move CSV
    # shutil.move(args.file, "csvs/" + args.file.replace("csvs\\", ""))
    # Create id_contacts Dictionary
    id_contacts_dict = create_id_contacts_dict(df, args.primary_key, args.columns)
    # Create is_valid_contacts Dictionary
    is_valid_contact_dict = {key: {"Number": 0, "Email": 0, "Extension": 0, "Name": 0} for key, _ in id_contacts_dict.items()}

    # Parse Contacts through OAI
    print("Calling OpenAI Fine-Tuned Model...")
    primary_contacts_dict = format_contacts_iteratively(id_contacts_dict)

    # Test OAI Contacts 
    # print("\nTesting OpenAI Fine-Tuned Model responses...")
    validation_tests = [
        test_name_in_original_string,
        test_name_format,
        test_extension_in_original_string,
        test_extension_format,
        test_extension_keyword_in_original_string,
        test_extension_found_within_phone_number,
        test_extension_present_without_phone_number,
    ]
    [test(id_contacts_dict, primary_contacts_dict, is_valid_contact_dict) for test in validation_tests]

    for key, value in primary_contacts_dict.items():
        print(f"{key}: {value}")

    for key, value in is_valid_contact_dict.items():
        print(f"{key}: {value}")
        [print(f"\t{error}") for error in primary_contacts_dict[key]["Errors"]]

    # PRINT TESTING RESULTS (CAN BE REMOVED LATER)
    # for key, value in is_valid_contact_dict.items():
    #     print("\tID: " + str(key) + "\t\tResult: " + str(value))

    # Check Values Still Valid
    # valid_id_contacts_dict = filter_invalid_values(primary_contacts_dict, is_valid_contact_dict)

    # Convert Back to DF
    # IMPLEMENTATION OF [convert_id_hours_dict_to_df] REQUIRED
    # if not os.path.isdir('csvs'):
    #     os.mkdir('csvs')
    # primary_contacts_df.to_csv("csvs/" + args.file.replace(".csv", "").replace("csvs\\", "") + "_PRIMARY_CONTACTS.csv")
