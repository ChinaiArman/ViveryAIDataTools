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
import re

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
Please find me the EMAIL ADDRESS from the following string, and append "%%" DIRECTLY after the email extension. 

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

!!! Do NOT use the phone number for the name, ONLY ALPHABETICAL CHARACTERS
!!! First and Last name must start with a capital letter.
!!! The output must contain two words, and have a space separating them.
!!! If there is no name present in the following text, return "NA" followed by "%%".

Input: "johnnyappleseed"
Output: Johnny Appleseed%%

Input: "John Cena, johncena@vivery.org, 603-654-4524"
Output: John Cena%%
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
        max_tokens=15,
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
        primary_contacts_dict[key]["Errors"] = ""
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


def convert_back_to_df(id_contacts_dict: dict, primary_contacts_dict: dict, is_valid_contact_dict: dict) -> pd.DataFrame:
    """
    """
    # primary_contacts_df = pd.DataFrame(columns=["ID", "Number", "Email", "Name", "Extension", "Original Data", "Notes"])

    primary_contacts_df = pd.concat([
        pd.DataFrame.from_dict(primary_contacts_dict, orient='index').reset_index(),
        pd.DataFrame.from_dict(is_valid_contact_dict, orient='index').reset_index().rename(columns={"Number": "NumberGrade", "Email": "EmailGrade", "Extension": "ExtensionGrade", "Name": "NameGrade"}),
        pd.DataFrame.from_dict(id_contacts_dict, orient='index').reset_index().rename(columns={0: "Data"})
    ], axis=1)
    primary_contacts_df = primary_contacts_df.loc[:,~primary_contacts_df.columns.duplicated()].copy()
    primary_contacts_df = primary_contacts_df.rename(columns={"index": "ID"})
    primary_contacts_df = primary_contacts_df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    primary_contacts_df = primary_contacts_df.style.apply(all_highlights, axis=1)
    return primary_contacts_df


def highlight_name_repair(primary_contacts_df: pd.DataFrame) -> pd.DataFrame:
    """
    """
    contacts_series = pd.Series(data=False, index=primary_contacts_df.index)
    contacts_series["Name"] = primary_contacts_df["NameGrade"] == -1
    return ['background-color: green' if value else '' for value in contacts_series]


def highlight_name_warnings(primary_contacts_df: pd.DataFrame) -> pd.DataFrame:
    """
    """
    contacts_series = pd.Series(data=False, index=primary_contacts_df.index)
    contacts_series["Name"] = primary_contacts_df["NameGrade"] == 1
    return ['background-color: yellow' if value else '' for value in contacts_series]


def highlight_name_errors(primary_contacts_df: pd.DataFrame) -> pd.DataFrame:
    """
    """
    contacts_series = pd.Series(data=False, index=primary_contacts_df.index)
    contacts_series["Name"] = primary_contacts_df["NameGrade"] == 2
    return ['background-color: red' if value else '' for value in contacts_series]


def highlight_extension_repair(primary_contacts_df: pd.DataFrame) -> pd.DataFrame:
    """
    """
    contacts_series = pd.Series(data=False, index=primary_contacts_df.index)
    contacts_series["Extension"] = primary_contacts_df["ExtensionGrade"] == -1
    return ['background-color: green' if value else '' for value in contacts_series]


def highlight_extension_warnings(primary_contacts_df: pd.DataFrame) -> pd.DataFrame:
    """
    """
    contacts_series = pd.Series(data=False, index=primary_contacts_df.index)
    contacts_series["Extension"] = primary_contacts_df["ExtensionGrade"] == 1
    return ['background-color: yellow' if value else '' for value in contacts_series]


def highlight_extension_errors(primary_contacts_df: pd.DataFrame) -> pd.DataFrame:
    """
    """
    contacts_series = pd.Series(data=False, index=primary_contacts_df.index)
    contacts_series["Extension"] = primary_contacts_df["ExtensionGrade"] == 2
    return ['background-color: red' if value else '' for value in contacts_series]


def highlight_number_repair(primary_contacts_df: pd.DataFrame) -> pd.DataFrame:
    """
    """
    contacts_series = pd.Series(data=False, index=primary_contacts_df.index)
    contacts_series["Number"] = primary_contacts_df["NumberGrade"] == -1
    return ['background-color: green' if value else '' for value in contacts_series]


def highlight_number_warnings(primary_contacts_df: pd.DataFrame) -> pd.DataFrame:
    """
    """
    contacts_series = pd.Series(data=False, index=primary_contacts_df.index)
    contacts_series["Number"] = primary_contacts_df["NumberGrade"] == 1
    return ['background-color: yellow' if value else '' for value in contacts_series]


def highlight_number_errors(primary_contacts_df: pd.DataFrame) -> pd.DataFrame:
    """
    """
    contacts_series = pd.Series(data=False, index=primary_contacts_df.index)
    contacts_series["Number"] = primary_contacts_df["NumberGrade"] == 2
    return ['background-color: red' if value else '' for value in contacts_series]


def highlight_email_repair(primary_contacts_df: pd.DataFrame) -> pd.DataFrame:
    """
    """
    contacts_series = pd.Series(data=False, index=primary_contacts_df.index)
    contacts_series["Email"] = primary_contacts_df["EmailGrade"] == -1
    return ['background-color: green' if value else '' for value in contacts_series]


def highlight_email_warnings(primary_contacts_df: pd.DataFrame) -> pd.DataFrame:
    """
    """
    contacts_series = pd.Series(data=False, index=primary_contacts_df.index)
    contacts_series["Email"] = primary_contacts_df["EmailGrade"] == 1
    return ['background-color: yellow' if value else '' for value in contacts_series]


def highlight_email_errors(primary_contacts_df: pd.DataFrame) -> pd.DataFrame:
    """
    """
    contacts_series = pd.Series(data=False, index=primary_contacts_df.index)
    contacts_series["Email"] = primary_contacts_df["EmailGrade"] == 2
    return ['background-color: red' if value else '' for value in contacts_series]


def all_highlights(primary_contacts_df: pd.DataFrame) -> pd.DataFrame:
    """
    """
    highlight_functions = {
        highlight_number_repair: 1,
        highlight_number_warnings: 1,
        highlight_number_errors: 1,
        highlight_email_repair: 2,
        highlight_email_warnings: 2,
        highlight_email_errors: 2,
        highlight_name_repair: 3,
        highlight_name_warnings: 3,
        highlight_name_errors: 3,
        highlight_extension_repair: 4,
        highlight_extension_warnings: 4,
        highlight_extension_errors: 4,
    }
    highlights = [''] * primary_contacts_df.size
    for function, index in highlight_functions.items():
        value = function(primary_contacts_df)[index]
        if value != '':
            highlights[index] = value
    return highlights




# TESTS
def test_name_in_original_string(id_contacts_dict: dict, primary_contacts_dict: dict, is_valid_contact_dict: dict) -> dict:
    """
    """
    for key, value in primary_contacts_dict.items():
        is_valid = True
        try:
            for name in value["Name"].split(" "):
                is_valid = (name in id_contacts_dict[key] or name == "NA") and is_valid
        except: 
            pass
        
        if not is_valid:
            is_valid_contact_dict[key]["Name"] = max(2, is_valid_contact_dict[key]["Name"])
            primary_contacts_dict[key]["Errors"] += "ERROR: Name not found within original contact information.\n"

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
            primary_contacts_dict[key]["Errors"] += "ERROR: Name formatting is not valid (FirstName LastName).\n"

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
            is_valid_contact_dict[key]["Extension"] = max(2, is_valid_contact_dict[key]["Extension"])
            primary_contacts_dict[key]["Errors"] += "ERROR: Extension not found within original contact information.\n"
        
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
            primary_contacts_dict[key]["Errors"] += "ERROR: Extension is not numerical.\n"
        
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
            primary_contacts_dict[key]["Errors"] += "WARNING: Extension Keyword not found within original contact information.\n"
        
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
            is_valid_contact_dict[key]["Extension"] = max(2, is_valid_contact_dict[key]["Extension"])
            primary_contacts_dict[key]["Errors"] += "ERROR: Extension found within phone number.\n"
        
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
            primary_contacts_dict[key]["Errors"] += "ERROR: Extension present without phone number.\n"
        
    return is_valid_contact_dict


def test_email_in_original_string(id_contacts_dict: dict, primary_contacts_dict: dict, is_valid_contact_dict: dict) -> dict:
    """
    """
    for key, value in primary_contacts_dict.items():
        is_valid = True
        try:
            is_valid = (value["Email"] in id_contacts_dict[key] or value["Email"] == "NA") and is_valid
        except:
            pass

        if not is_valid:
            is_valid_contact_dict[key]["Email"] = max(2, is_valid_contact_dict[key]["Email"])
            primary_contacts_dict[key]["Errors"] += "ERROR: Email not found within original contact information.\n"
        
    return is_valid_contact_dict


def test_email_format(_: dict, primary_contacts_dict: dict, is_valid_contact_dict: dict) -> dict:
    """
    """
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    for key, value in primary_contacts_dict.items():
        is_valid = True
        try:
            if not re.fullmatch(regex, value["Email"]) and value["Email"] != "NA":
                is_valid = False
        except:
            if value["Email"] != "NA":
                is_valid = False

        if not is_valid:
            is_valid_contact_dict[key]["Email"] = max(2, is_valid_contact_dict[key]["Email"])
            primary_contacts_dict[key]["Errors"] += "ERROR: Email formatting is not valid ([prefix]@[domain].[extension]).\n"

    return is_valid_contact_dict


def test_phone_in_original_string(id_contacts_dict: dict, primary_contacts_dict: dict, is_valid_contact_dict: dict) -> dict:
    """
    """
    for key, value in primary_contacts_dict.items():
        is_valid = True
        try:
            is_valid = (value["Number"].replace("-", "") in id_contacts_dict[key].replace("-", "").replace("(", "").replace(")", "").replace(" ", "") or value["Number"] == "NA") and is_valid
        except:
            pass

        if not is_valid:
            is_valid_contact_dict[key]["Number"] = max(2, is_valid_contact_dict[key]["Number"])
            primary_contacts_dict[key]["Errors"] += "ERROR: Number not found within original contact information.\n"
        
    return is_valid_contact_dict


def test_phone_format(_: dict, primary_contacts_dict: dict, is_valid_contact_dict: dict) -> dict:
    """
    """
    regex = r'^[0-9]{3}[-][0-9]{3}[-][0-9]{4}$'
    for key, value in primary_contacts_dict.items():
        is_valid = True
        try:
            if not re.fullmatch(regex, value["Number"]) and value["Number"] != "NA":
                is_valid = False
        except:
            if value["Number"] != "NA":
                is_valid = False

        if not is_valid:
            is_valid_contact_dict[key]["Number"] = max(2, is_valid_contact_dict[key]["Number"])
            primary_contacts_dict[key]["Errors"] += "ERROR: Number formatting is not valid (###-###-####).\n"

    return is_valid_contact_dict




# REPAIR
def repair_extension(_: dict, primary_contacts_dict: dict, is_valid_contact_dict: dict) -> None:
    """
    """
    for key, value in primary_contacts_dict.items():
        if is_valid_contact_dict[key]["Extension"] > 0:
            value["Extension"] = "NA"
            is_valid_contact_dict[key]["Extension"] = -1
    return


def repair_email(id_contacts_dict: dict, primary_contacts_dict: dict, is_valid_contact_dict: dict) -> None:
    """
    """
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    for key, value in primary_contacts_dict.items():
        if is_valid_contact_dict[key]["Email"] > 0 or value["Email"] == "NA":
            email = re.findall(regex, id_contacts_dict[key])
            if len(email) == 0:
                email = ["NA"]
            if email[0] != value["Email"]:
                value["Email"] = "/".join(email)
                is_valid_contact_dict[key]["Email"] = -1
    return


def repair_name(id_contacts_dict: dict, primary_contacts_dict: dict, is_valid_contact_dict: dict) -> None:
    """
    """
    for key, value in primary_contacts_dict.items():
        if is_valid_contact_dict[key]["Name"] > 0 or value["Name"] == "NA":
            contact = id_contacts_dict[key]
            contact = contact.replace(value["Email"], "").replace(value["Number"], "").replace(value["Extension"], "").replace(",", "")
            contact = call_oai(PROMPTS["Name"], contact)
            try:
                int(contact)
                contact = "NA"
            except:
                pass
            if value["Name"] != contact:
                value["Name"] = contact
                is_valid_contact_dict[key]["Name"] = -1
    return


def repair_number(id_contacts_dict: dict, primary_contacts_dict: dict, is_valid_contact_dict: dict) -> None:
    """
    """
    regex = r'^[0-9]{3}[-][0-9]{3}[-][0-9]{4}$'
    for key, value in primary_contacts_dict.items():
        if is_valid_contact_dict[key]["Number"] > 0 or value["Number"] == "NA":
            number = re.findall(regex, id_contacts_dict[key])
            if len(number) == 0:
                number = ["NA"]
            if number[0] != value["Number"]:
                value["Number"] = "/".join(number)
                is_valid_contact_dict[key]["Number"] = -1
    return




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
    # Add column arguments
    parser.add_argument("--repair", action="store", help="A flag indicating whether repair mode is on")
    # Console arguments
    args = parser.parse_args()

    # Create DataFrame
    if '.xlsx' in args.file:
        df = pd.read_excel(args.file)
    else:
        df = pd.read_csv(args.file)
    # Move CSV
    shutil.move(args.file, "datafiles/" + args.file.replace("datafiles\\", ""))
    # Create id_contacts Dictionary
    id_contacts_dict = create_id_contacts_dict(df, args.primary_key, args.columns)
    # Create is_valid_contacts Dictionary
    is_valid_contact_dict = {key: {"Number": 0, "Email": 0, "Extension": 0, "Name": 0} for key, _ in id_contacts_dict.items()}

    # Parse Contacts through OAI
    print("Calling OpenAI Fine-Tuned Model...")
    primary_contacts_dict = format_contacts_iteratively(id_contacts_dict)

    # Test OAI Contacts 
    print("\nTesting OpenAI Fine-Tuned Model responses...")
    validation_tests = [
        test_name_in_original_string,
        test_name_format,
        test_extension_in_original_string,
        test_extension_format,
        test_extension_keyword_in_original_string,
        test_extension_found_within_phone_number,
        test_extension_present_without_phone_number,
        test_email_in_original_string,
        test_email_format,
        test_phone_in_original_string,
        test_phone_format,
    ]
    [test(id_contacts_dict, primary_contacts_dict, is_valid_contact_dict) for test in validation_tests]

    for key, value in primary_contacts_dict.items():
        print(f"{key}: {value}")

    for key, value in is_valid_contact_dict.items():
        print(f"{key}: {value}")
        print(primary_contacts_dict[key]["Errors"])

    # Execute repair script
    if bool(args.repair):
        print("Executing Repair Script...")
        repair_extension(id_contacts_dict, primary_contacts_dict, is_valid_contact_dict)
        repair_email(id_contacts_dict, primary_contacts_dict, is_valid_contact_dict)
        repair_number(id_contacts_dict, primary_contacts_dict, is_valid_contact_dict)
        repair_name(id_contacts_dict, primary_contacts_dict, is_valid_contact_dict)
        for key, value in primary_contacts_dict.items():
            value["Errors"] = ""
        [test(id_contacts_dict, primary_contacts_dict, is_valid_contact_dict) for test in validation_tests]

    # Save File
    final_styled_df = convert_back_to_df(id_contacts_dict, primary_contacts_dict, is_valid_contact_dict)
    if not os.path.isdir('datafiles'):
        os.mkdir('datafiles')
    final_styled_df.to_excel("datafiles/" + args.file.replace(".csv", "").replace(".xlsx", "").replace("datafiles\\", "") + "_PRIMARY_CONTACTS.xlsx")
