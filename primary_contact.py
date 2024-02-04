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
PROMPT = """
Given an input string, create the following output dictionary:

"
{
    "P#": [phone_number],
    "P#Ext": [phone_number_extension],
    "Email": [email],
    "Name": [name],
    "Marker": [marker]
}
"

Keys:
P# will contain a phone number if present, else None. Phone numbers must be stored using the following format, with X representing the phone number digits: XXX-XXX-XXXX
P#Ext will contain a phone number extension if present, else None. 
Email will contain an email address if present, else None.
Name will contain a name if present, else None.
Marker will be a boolean value (True/False). Marker is True if there are multiple values present for any of the above keys, or if the value for all keys is None. Otherwise, marker is False.

Formatting Notes:
Do not include information that does not fall into one of the above keys.
Do not use any tokens from outside of the input string.
Use None for any values that are not present in the input string.
!!! Do NOT attempt to generation information to fill the keys, if no phone number is present, do not include a phone number, only None for missing values.
!!! ALL Keys must be present in the dictionary, even if their value is None.
!!! The value for Name must be formatted in FirstName LastName, else None.
"""




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


def call_oai(prompt: str) -> str:
    """
    """
    print(f"IN: {prompt}")
    openai.api_type = "azure"
    openai.api_base = OAI_API["base"]
    openai.api_version = "2023-09-15-preview"
    openai.api_key = OAI_API["key"]
    response = openai.Completion.create(
        engine=OAI_API["engine"],
        prompt=f"{PROMPT}\Input String: {prompt}\nOutput Dictionary: ",
        temperature=0.4,
        max_tokens=50,
        top_p=0.25,
        frequency_penalty=0,
        presence_penalty=0,
        best_of=2,
        stop=["}"]
    )
    time.sleep(0.05)
    print("\tOAI API Response: " + response["choices"][0]["text"])
    return response["choices"][0]["text"] + "}"


def format_contacts_iteratively(id_contacts_dict: dict) -> dict:
    """
    """
    primary_contacts_dict = {}
    for key, value in id_contacts_dict.items():
        new_value = call_oai(value)
        try:
            new_value = eval(new_value.replace("\n", ""))
        except:
            pass
        primary_contacts_dict[key] = new_value
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




# WEAK WARNING TESTS




# STRONG WARNING TESTS




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
    is_valid_contact_dict = {key: True for key, _ in id_contacts_dict.items()}

    # Parse Contacts through OAI
    print("Calling OpenAI Fine-Tuned Model...")
    primary_contacts_dict = format_contacts_iteratively(id_contacts_dict)

    # Test OAI Contacts 
    print("\nTesting OpenAI Fine-Tuned Model responses...")
    validation_tests = [
    ]
    [test(id_contacts_dict, primary_contacts_dict, is_valid_contact_dict) for test in validation_tests]

    # PRINT TESTING RESULTS (CAN BE REMOVED LATER)
    for key, value in is_valid_contact_dict.items():
        print("\tID: " + str(key) + "\t\tResult: " + str(value))

    # Check Values Still Valid
    # valid_id_contacts_dict = filter_invalid_values(primary_contacts_dict, is_valid_contact_dict)

    # Convert Back to DF
    # IMPLEMENTATION OF [convert_id_hours_dict_to_df] REQUIRED
    # if not os.path.isdir('csvs'):
    #     os.mkdir('csvs')
    # primary_contacts_df.to_csv("csvs/" + args.file.replace(".csv", "").replace("csvs\\", "") + "_PRIMARY_CONTACTS.csv")
