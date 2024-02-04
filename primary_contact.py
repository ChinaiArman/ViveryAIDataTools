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

# LOCAL FILE IMPORTS


# AI CONSTANTS
from keys import PRIMARY_CONTACT_KEY as OAI_API

# MISC CONSTANTS
PROMPTS = {
"Number": 
"""
Extract the phone from the following string, and append "%%" DIRECTLY after the number. 

!!! Format the number using the following format: "XXX-XXX-XXXX%%", with "X" representing a digit 0-9.
!!! If there is no phone number present in the following text, return "NA" followed by "%%"

Input: "(513)-153-5915, johnnyappleseed@gmail.com"
Output: 513-153-5915%%
""",
"Email": 
"""
Extract the email from the following string, and append "%%" DIRECTLY after the email domain. 

!!! Format the email using the following format: "[prefix]@[domain].[extension]%%".
!!! If there is NO EMAIL PRESENT in the following text, return "NA" followed by "%%"

Input: "513-153-5915, johnnyappleseed@gmail.com"
Output: johnnyappleseed@gmail.com%%

Input: "joannepeach53@gmail.com"
Output: joannepeach53@gmail.com%%
""",
"Name": 
"""
Extract the first and last name of this persons from their contact information in the following string, and append "%%" DIRECTLY after the number. 

!!! Do NOT use numbers or symbols in the output.
!!! First and Last name must start with a capital letter.
!!! The output must contain two words, and have a space separating them.
!!! If there is no name present in the following text, return "NA" followed by "%%".

Input: "513-153-5915, johnnyappleseed@gmail.com"
Output: Johnny Appleseed%%
""",
"Extension": 
"""
Extract the phone extension from the following string, and append "%%" DIRECTLY after the number. 

!!! Format the extension using the following format: "XXXX%%", with "X" representing a digit 0-9. The number of digits depends on the length of the phone extension.
!!! If there is no extension present in the following text, return "NA" followed by "%%"
!!! DO NOT INCLUDE NUMBERS THAT ARE APART OF EMAIL ADDRESSES OR THE BASE PHONE NUMBER, ONLY NUMBERS CLEARLY MARKED AS EXTENSIONS.

Input: "513-153-5915 EXT 5315, johnnyappleseed19845@gmail.com"
Output: 5315%%

Input: "158-159-0915, joannepeach53@gmail.com Joanne Peach"
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
        id_contacts_dict[row[primary_key]] = ", ".join(row[contact_columns].tolist()).strip()
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
        best_of=1,
        stop=["%%"]
    )
    time.sleep(0.05)
    print("\tOAI API Response: " + response["choices"][0]["text"])
    return response["choices"][0]["text"]


def format_contacts_iteratively(id_contacts_dict: dict) -> dict:
    """
    """
    primary_contacts_dict = {}
    for key, value in id_contacts_dict.items():
        primary_contacts_dict[key] = {prompt_type: call_oai(prompt, value) for prompt_type, prompt in PROMPTS.items()}
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
    # for key, value in primary_contacts_dict.items():
    #     is_valid = True
    #     try:
    #         for name in value["Name"].split(" "):
    #             is_valid = name.lower().replace(" ", "") in id_contacts_dict[key].lower().replace(" ", "") and is_valid
    #     except: 
    #         is_valid = True
    #     is_valid_contact_dict[key] = is_valid_contact_dict[key] and is_valid
    return is_valid_contact_dict


def test_name_format(_: dict, primary_contacts_dict: dict, is_valid_contact_dict: dict) -> dict:
    """
    """
    # for key, value in primary_contacts_dict.items():
    #     is_valid = True
    #     try:
    #         is_valid = value["Name"].replace(" ", "").isalpha() and is_valid
    #         for name in value["Name"].split(" "):
    #             is_valid = name.replace(" ", "")[0].isupper() and is_valid
    #     except: 
    #         is_valid = True
    #     is_valid_contact_dict[key] = is_valid_contact_dict[key] and is_valid
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
    is_valid_contact_dict = {key: {"Number": True, "Email": True, "Extension": True, "Name": True} for key, _ in id_contacts_dict.items()}

    # Parse Contacts through OAI
    print("Calling OpenAI Fine-Tuned Model...")
    primary_contacts_dict = format_contacts_iteratively(id_contacts_dict)
    for key, value in primary_contacts_dict.items():
        print(f"{key}: {value}")

    # Test OAI Contacts 
    # print("\nTesting OpenAI Fine-Tuned Model responses...")
    validation_tests = [
        test_name_in_original_string,
        test_name_format,
    ]
    # [test(id_contacts_dict, primary_contacts_dict, is_valid_contact_dict) for test in validation_tests]

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
