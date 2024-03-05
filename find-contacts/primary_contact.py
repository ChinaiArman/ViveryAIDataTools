"""
Primary Contacts Script

@author Arman Chinai
@version 1.0.1

This script uses Azure OpenAI to isolate contact information pieces into separate columns. 
The input of this program is an excel or CSV file containing contact information and IDs.
The output of this file is an annotated excel file with the contact information separated.
The contacts are parsed line-by-line to a Davinci Azure OpenAI model.
The resulting contacts are then tested for AI errors, with failing contacts being flagged for manual review.
The program has a repair mode which attempts to fix any failed contact information.
The output is then converted to an excel file, with highlights to indicate which cells need to be manually reviewed.

---> OPERATIONAL INSTRUCTIONS <---

Package Imports:
    * OpenAI            * Pandas            * Time
    * Argparse          * Regex             

API Keys (stored in keys.py):
    * Azure OpenAI - North Central US: Contact Arman for API Key.

Instructions:
    1) Package Imports:
        a) Create a new terminal.
        b) Run `pip install -r requirements.txt`.
    2) API Keys:
        a) Create a new file `keys.py` within the directory at the same level as `primary_contact.py`.
        b) Contact Arman (arman@vivery.org) for the API Key.
        c) Create a new python variable `PRIMARY_CONTACT_KEY` with the received API Key.
    3) Add an excel or csv file to the repository:
        a) File must contain IDs for each row.
    4) Run the following command within the terminal: `python primary_contact.py "{path to excel/csv file from working directory}, {primary key} --columns {columns, delimited by a comma} --repair TRUE"`.

Desired Output:
    * A new Excel file will be present within the working directory, with the name ending in "_PRIMARY_CONTACTS.xlsx".
    * The file will contain the contacts for each id separated into their respective columns.
    * Any hours that failed the testing round will be highlighted in red or yellow to indicate the severity of the error.
    * Cells highlighted in green or with no highlight are error free, and can be assumed valid.

Still have questions? Send an email to `arman@abimpacttech.com` with the subject line `Primary Contact - {question}`.
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
    Splits a comma-separated string in the CL Arguments into a list of strings.

    Args:
        arg (str): A comma-separated string from the CL Arguments.

    Returns:
        list: A list of strings obtained by splitting the input string at each comma.

    Example:
        >>> result = list_of_strings("apple,orange,banana")
        >>> print(result)
        ['apple', 'orange', 'banana']

    Note:
        Used to split the columns from the CL Arguments.
        This function assumes that the input string contains elements separated by commas.
        The resulting list may contain empty strings if there are consecutive commas in the input.
    """
    return arg.split(',')


def create_id_contacts_dict(df: pd.DataFrame, primary_key: str, contact_columns: list) -> dict:
    """
    Creates a dictionary mapping unique identifiers to concatenated contact information.

    Args:
        df (pd.DataFrame): The DataFrame containing the data.
        primary_key (str): The primary key column name used as the unique identifier.
        contact_columns (list): A list of column names containing contact information.

    Returns:
        dict: A dictionary where keys are unique identifiers, and values are concatenated
              strings of contact information from specified columns.

    Example:
        >>> data = pd.DataFrame({
        ...     'ID': [1, 2, 3],
        ...     'Name': ['John', 'Jane', 'Bob'],
        ...     'Email': ['john@example.com', 'jane@example.com', 'bob@example.com'],
        ...     'Phone': ['123-456-7890', '987-654-3210', 'NA']
        ... })
        >>> contacts_dict = create_id_contacts_dict(data, 'ID', ['Name', 'Email', 'Phone'])
        >>> print(contacts_dict)
        {1: 'John, john@example.com, 123-456-7890',
         2: 'Jane, jane@example.com, 987-654-3210',
         3: 'Bob, bob@example.com, NA'}

    Note:
        This function assumes that the DataFrame has columns specified by primary_key and contact_columns.
        NA values are filled with the string "NA" for consistency in the concatenated result.
    """
    id_contacts_dict = {}
    for _, row in df.iterrows():
        row = row.fillna("NA")
        id_contacts_dict[row[primary_key]] = ", ".join(list(row[contact_columns])).strip()
    return id_contacts_dict


def call_oai(prompt: str, case: str) -> str:
    """
    Calls the Azure OpenAI engine with a given prompt and case to generate a response.

    Args:
        prompt (str): The prompt to be sent to the Azure OpenAI engine.
        case (str): The case to be included in the input prompt.

    Returns:
        str: The generated text response from the Azure OpenAI engine.

    Example:
        >>> response = call_oai("Generate a summary for the following case:", "A patient presents with...")
        >>> print(response)
        'The generated summary for the case...'

    Note:
        Sleeps thread briefly to prevent surpassing the limit on api calls per minute.
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
    Iteratively formats contact information using the Azure OpenAI engine prompts.

    Args:
        id_contacts_dict (dict): A dictionary containing program IDs as keys and contact information as values.

    Returns:
        dict: A dictionary containing formatted contact information generated by the Azure OpenAI engine prompts.

    Example:
        >>> formatted_contacts = format_contacts_iteratively({
        ...     'program_id_1': 'John Doe, johndoe@example.com, 123-456-7890',
        ...     'program_id_2': 'Jane Smith, janesmith@example.com, 987-654-3210'
        ... })
        >>> print(formatted_contacts)
        {
            'program_id_1': {
                'Name': 'The extracted name from contact information.',
                'Email': 'The extracted email from contact information.',
                'Phone': 'The extracted phone number from contact information.',
                'Errors': ''  # Any errors encountered during formatting.
            },
            'program_id_2': {
                'Name': 'The extracted name from contact information.',
                'Email': 'The extracted email from contact information.',
                'Phone': 'The extracted phone number from contact information.',
                'Errors': ''  # Any errors encountered during formatting.
            },
        }

    Note:
        Uses the call_oai function to create the formatted contacts as a dictionary to be tested.
    """
    primary_contacts_dict = {}
    for key, value in id_contacts_dict.items():
        primary_contacts_dict[key] = {prompt_type: call_oai(prompt, value) for prompt_type, prompt in PROMPTS.items()}
        primary_contacts_dict[key]["Errors"] = ""
    return primary_contacts_dict


def convert_back_to_df(id_contacts_dict: dict, primary_contacts_dict: dict, is_valid_contact_dict: dict) -> pd.DataFrame:
    """
    Converts contact dictionaries into a formatted Pandas DataFrame.

    Args:
        id_contacts_dict (dict): A dictionary containing program IDs as keys and raw contact information as values.
        primary_contacts_dict (dict): A dictionary containing program IDs as keys and formatted contact information as values.
        is_valid_contact_dict (dict): A dictionary containing program IDs as keys and boolean values indicating the validity of contact information.

    Returns:
        pd.DataFrame: A styled Pandas DataFrame containing formatted contact information for display.

    Note:
        Return output is a styled DataFrame, which highlights erroneous/repaired errors. Can be converted to excel at this point with the styles.
        Red highlight represents error, Yellow highlight represents warning, Green highlight represents repaired values.
    """
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


def all_highlights(primary_contacts_df: pd.DataFrame) -> list:
    """
    Applies various highlight functions to a Pandas DataFrame and returns a highlight matrix.

    Args:
        primary_contacts_df (pd.DataFrame): The Pandas DataFrame containing contact information.

    Returns:
        list: A list with the highlight matrix representing which cells need to be highlighted with which colour.

    Note:
        This function combines highlights from different functions into a single DataFrame.
        The highlights are generated based on their validity scores after testing/repairing.
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
    Tests whether each name in the "Name" field is found within the original contact information.

    Args:
        id_contacts_dict (dict): Dictionary containing original contact information.
        primary_contacts_dict (dict): Dictionary containing processed contact information.
        is_valid_contact_dict (dict): Dictionary indicating the validity of each contact entry.

    Returns:
        dict: Updated is_valid_contact_dict with Name validation results.

    Note:
        Assigns an error code of 2 if the test fails.
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
    Tests whether each name in the "Name" field is of a valid name format.

    Args:
        id_contacts_dict (dict): Dictionary containing original contact information.
        primary_contacts_dict (dict): Dictionary containing processed contact information.
        is_valid_contact_dict (dict): Dictionary indicating the validity of each contact entry.

    Returns:
        dict: Updated is_valid_contact_dict with Name validation results.

    Note:
        Assigns an error code of 2 if the test fails.
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
    Tests whether each extension in the "Extension" field is found within the original contact information.

    Args:
        id_contacts_dict (dict): Dictionary containing original contact information.
        primary_contacts_dict (dict): Dictionary containing processed contact information.
        is_valid_contact_dict (dict): Dictionary indicating the validity of each contact entry.

    Returns:
        dict: Updated is_valid_contact_dict with Extension validation results.

    Note:
        Assigns an error code of 2 if the test fails.
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
    Tests whether each extension in the "Extension" field is of a valid extension format.

    Args:
        id_contacts_dict (dict): Dictionary containing original contact information.
        primary_contacts_dict (dict): Dictionary containing processed contact information.
        is_valid_contact_dict (dict): Dictionary indicating the validity of each contact entry.

    Returns:
        dict: Updated is_valid_contact_dict with Extension validation results.

    Note:
        Assigns an error code of 2 if the test fails.
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
    Tests whether each extension in the "Extension" field contains an extension key word.

    Args:
        id_contacts_dict (dict): Dictionary containing original contact information.
        primary_contacts_dict (dict): Dictionary containing processed contact information.
        is_valid_contact_dict (dict): Dictionary indicating the validity of each contact entry.

    Returns:
        dict: Updated is_valid_contact_dict with Name validation results.

    Note:
        Assigns an error code of 1 if the test fails.
        Extension key words are terms like EXT., Extension, etc.
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
    Tests whether each extension in the "Extension" field is not contained within the phone number.

    Args:
        id_contacts_dict (dict): Dictionary containing original contact information.
        primary_contacts_dict (dict): Dictionary containing processed contact information.
        is_valid_contact_dict (dict): Dictionary indicating the validity of each contact entry.

    Returns:
        dict: Updated is_valid_contact_dict with Extension validation results.

    Note:
        Assigns an error code of 2 if the test fails.
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
    Tests whether each row with an extension present in the "Extension" field also has a phone number present in the "Number" field.

    Args:
        id_contacts_dict (dict): Dictionary containing original contact information.
        primary_contacts_dict (dict): Dictionary containing processed contact information.
        is_valid_contact_dict (dict): Dictionary indicating the validity of each contact entry.

    Returns:
        dict: Updated is_valid_contact_dict with Extension validation results.

    Note:
        Assigns an error code of 2 if the test fails.
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
    Tests whether each email in the "Email" field is in the original contact string.

    Args:
        id_contacts_dict (dict): Dictionary containing original contact information.
        primary_contacts_dict (dict): Dictionary containing processed contact information.
        is_valid_contact_dict (dict): Dictionary indicating the validity of each contact entry.

    Returns:
        dict: Updated is_valid_contact_dict with Email validation results.

    Note:
        Assigns an error code of 2 if the test fails.
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
    Tests whether each email in the "Email" field is of a valid email format.

    Args:
        id_contacts_dict (dict): Dictionary containing original contact information.
        primary_contacts_dict (dict): Dictionary containing processed contact information.
        is_valid_contact_dict (dict): Dictionary indicating the validity of each contact entry.

    Returns:
        dict: Updated is_valid_contact_dict with Email validation results.

    Note:
        Assigns an error code of 2 if the test fails.
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
    Tests whether each phone number in the "Number" field is in the original contact string.

    Args:
        id_contacts_dict (dict): Dictionary containing original contact information.
        primary_contacts_dict (dict): Dictionary containing processed contact information.
        is_valid_contact_dict (dict): Dictionary indicating the validity of each contact entry.

    Returns:
        dict: Updated is_valid_contact_dict with Number validation results.

    Note:
        Assigns an error code of 2 if the test fails.
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
    Tests whether each phone number in the "Number" field is of a valid phone number format.

    Args:
        id_contacts_dict (dict): Dictionary containing original contact information.
        primary_contacts_dict (dict): Dictionary containing processed contact information.
        is_valid_contact_dict (dict): Dictionary indicating the validity of each contact entry.

    Returns:
        dict: Updated is_valid_contact_dict with Number validation results.

    Note:
        Assigns an error code of 2 if the test fails.
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
    Repairs the "Extension" field in contact information for entries with extension errors.

    Args:
        _: Placeholder argument, not used in the function.
        primary_contacts_dict (dict): Dictionary containing processed contact information.
        is_valid_contact_dict (dict): Dictionary indicating the validity of each contact entry.

    Returns:
        None: The function modifies the primary_contacts_dict and is_valid_contact_dict in place.

    Note:
        This function is designed to repair the "Extension" field for entries with extension errors.
        If the "Extension" validity score is greater than 0 (indicating an error), the field is set to "NA" to resolve the error.
        The validity score for the "Extension" field is then updated to -1 to indicate that it has been repaired.
    """
    for key, value in primary_contacts_dict.items():
        if is_valid_contact_dict[key]["Extension"] > 0:
            value["Extension"] = "NA"
            is_valid_contact_dict[key]["Extension"] = -1
    return


def repair_email(id_contacts_dict: dict, primary_contacts_dict: dict, is_valid_contact_dict: dict) -> None:
    """
    Repairs the "Email" field in contact information for entries with email errors.

    Args:
        id_contacts_dict (dict): Original dictionary containing raw contact information.
        primary_contacts_dict (dict): Dictionary containing processed contact information.
        is_valid_contact_dict (dict): Dictionary indicating the validity of each contact entry.

    Returns:
        None: The function modifies the primary_contacts_dict and is_valid_contact_dict in place.

    Note:
        This function is designed to repair the "Email" field for entries with email errors.
        If the "Email" validity score is greater than 0 (indicating an error) or the processed value is "NA,"
        the function attempts to extract a valid email address from the original raw data (id_contacts_dict).
        The validity score for the "Email" field is then updated to -1 to indicate that it has been repaired.
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
    Repairs the "Name" field in contact information for entries with name errors.

    Args:
        id_contacts_dict (dict): Original dictionary containing raw contact information.
        primary_contacts_dict (dict): Dictionary containing processed contact information.
        is_valid_contact_dict (dict): Dictionary indicating the validity of each contact entry.

    Returns:
        None: The function modifies the primary_contacts_dict and is_valid_contact_dict in place.

    Note:
        This function is designed to repair the "Name" field for entries with name errors.
        If the "Name" validity score is greater than 0 (indicating an error) or the processed value is "NA,"
        the function extracts the contact information from the original raw data (id_contacts_dict),
        excluding the "Email," "Number," "Extension," and commas. It then uses OpenAI API to repair the name.
        If the repaired name is a numeric value, it is set to "NA."
        The validity score for the "Name" field is updated to -1 to indicate that it has been repaired.
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
    Repairs the "Number" field in contact information for entries with number errors.

    Args:
        id_contacts_dict (dict): Original dictionary containing raw contact information.
        primary_contacts_dict (dict): Dictionary containing processed contact information.
        is_valid_contact_dict (dict): Dictionary indicating the validity of each contact entry.

    Returns:
        None: The function modifies the primary_contacts_dict and is_valid_contact_dict in place.

    Note:
        This function is designed to repair the "Number" field for entries with number errors.
        If the "Number" validity score is greater than 0 (indicating an error) or the processed value is "NA,"
        the function extracts the contact information from the original raw data (id_contacts_dict).
        It then uses a regular expression to find a valid phone number pattern in the raw data.
        If a valid phone number is found, it is set as the repaired "Number" value.
        The validity score for the "Number" field is updated to -1 to indicate that it has been repaired.
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

