"""
"""


# PACKAGE IMPORTS
import openai
import argparse, os, shutil
import pandas as pd
import re
from datetime import datetime

# LOCAL FILE IMPORTS


# IMPORT CONSTANTS
from keys import API_KEY

# MISC CONSTANTS
INT_TO_DAY_OF_MONTH = {"1": ["1st", "First"], "2": ["2nd"], "3": ["3rd"], "4": ["4th"], "5": ["5th"], "": ""}
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
HOUR_TYPES = ["Weekly", "Day of Month", "Week of Month"]




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
        prompt=f"{prompt}",
        temperature=0.4,
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
        new_value = new_value
        cleaned_hours_dict[key] = new_value
    
    return cleaned_hours_dict


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
    # Create new DF
    cleaned_hours_df = pd.DataFrame(columns=df.columns)

    # Iterate over Program IDs
    for id in df["Program External ID"].to_list():
        new_entries = []
        row = df.loc[df['Program External ID'] == id].values.tolist()[0]

        # Create new row if valid cleaning
        if is_valid_hours_dict[id]:
            row = row[0:len(df.columns) - 15]
            list_of_entries = cleaned_hours_dict[id].split(";")
            for entry in list_of_entries:
                entry = entry.split(',')
                entry = row + entry + [""]
                new_entries.append(entry)

        # Add row to new DF
        if is_valid_hours_dict[id]:
            for entry in new_entries:
                try:
                    cleaned_hours_df.loc[len(cleaned_hours_df)] = entry
                except ValueError:
                    cleaned_hours_df.loc[len(cleaned_hours_df)] = row + [""] * 15
        else:
            cleaned_hours_df.loc[len(cleaned_hours_df)] = row
    
    # Return DF
    cleaned_hours_df.to_csv("test.csv")
    return cleaned_hours_df




# TESTS
def test_valid_day_of_week(_: dict, cleaned_hours_dict: dict, is_valid_dict: dict) -> dict:
    """
    """
    for key, value in cleaned_hours_dict.items():
        is_valid = True
        list_of_entries = value.split(";")

        for value in list_of_entries:
            value = value.split(",")
            is_valid = value[0] in DAYS_OF_WEEK and is_valid

        is_valid_dict[key] = is_valid_dict[key] and is_valid

    return is_valid_dict


def test_valid_entry_format(_: dict, cleaned_hours_dict: dict, is_valid_dict: dict) -> dict:
    """
    """
    for key, value in cleaned_hours_dict.items():
        count_semicolons = value.count(";")
        count_commas = value.count(",")
        is_valid = 13 + count_semicolons * 13 == count_commas
        is_valid_dict[key] = is_valid_dict[key] and is_valid

    return is_valid_dict


# def test_number_of_days_greater_than_entries(id_hours_dict: dict, cleaned_hours_dict: dict, is_valid_dict: dict) -> dict:
#     """
#     """
#     for key, value in cleaned_hours_dict.items():
#         number_of_entries = len(value.split(";"))
#         number_of_days = 0

#         for day in DAYS_OF_WEEK:
#             number_of_days += day in id_hours_dict[key]

#         is_valid_dict[key] = is_valid_dict[key] and number_of_entries >= number_of_days

#     return is_valid_dict


def test_valid_open_closed_hours(_: dict, cleaned_hours_dict: dict, is_valid_dict: dict) -> dict:
    """
    """
    time_regex = re.compile("^([01]?[0-9]|2[0-3]):[0-5][0-9]$")

    for key, value in cleaned_hours_dict.items():
        is_valid = True
        list_of_entries = value.split(";")

        for value in list_of_entries:
            value = value.split(",")
            is_valid = value[1] != "" and value[2] != "" and is_valid
            is_open_hour_valid = re.search(time_regex, value[1])
            is_closed_hour_valid = re.search(time_regex, value[2])
            is_valid = is_open_hour_valid != None and is_closed_hour_valid != None and is_valid

        is_valid_dict[key] = is_valid_dict[key] and is_valid
    
    return is_valid_dict
            

def test_close_hour_greater_than_open_hour(_: dict, cleaned_hours_dict: dict, is_valid_dict: dict) -> dict:
    """
    """
    for key, value in cleaned_hours_dict.items():
        is_valid = True
        list_of_entries = value.split(";")

        for value in list_of_entries:
            value = value.split(",")
            is_valid = datetime.strptime(value[2], "%H:%M") > datetime.strptime(value[1], "%H:%M") and is_valid

        is_valid_dict[key] = is_valid_dict[key] and is_valid

    return is_valid_dict


def test_day_of_month_formatting(_: dict, cleaned_hours_dict: dict, is_valid_dict: dict) -> dict:
    """
    """
    for key, value in cleaned_hours_dict.items():
        is_valid = True
        list_of_entries = value.split(";")

        for value in list_of_entries:
            value = value.split(",")
            is_valid = value[10] == "Day of Month" and value[9].isdigit() and value[8] == "" and is_valid
            try:
                is_valid = (any(day_of_month_value in id_hours_dict[key] for day_of_month_value in INT_TO_DAY_OF_MONTH[value[9]]) or value[9] == "") and is_valid
            except:
                is_valid = False

        is_valid_dict[key] = is_valid_dict[key] and is_valid

    return is_valid_dict


def test_week_of_month_formatting(_: dict, cleaned_hours_dict: dict, is_valid_dict: dict) -> dict:
    """
    """
    for key, value in cleaned_hours_dict.items():
        is_valid = True
        list_of_entries = value.split(";")

        for value in list_of_entries:
            value = value.split(",")
            is_valid = value[10] == "Week of Month" and value[8].isdigit() and value[9] == "" and is_valid
            try:
                is_valid = (any(day_of_week_value in id_hours_dict[key] for day_of_week_value in INT_TO_DAY_OF_MONTH[value[8]]) or value[8] == "") and is_valid
            except:
                is_valid = False

        is_valid_dict[key] = is_valid_dict[key] and is_valid

    return is_valid_dict


def test_weekly_formatting(_: dict, cleaned_hours_dict: dict, is_valid_dict: dict) -> dict:
    """
    """
    for key, value in cleaned_hours_dict.items():
        is_valid = True
        list_of_entries = value.split(";")

        for value in list_of_entries:
            value = value.split(",")
            is_valid = value[10] == "Weekly" and value[8] == "" and value[9] == "" and is_valid

        is_valid_dict[key] = is_valid_dict[key] and is_valid

    return is_valid_dict


def test_all_null_values_empty_string(_: dict, cleaned_hours_dict: dict, is_valid_dict: dict) -> dict:
    """
    """
    for key, value in cleaned_hours_dict.items():
        is_valid = True
        list_of_entries = value.split(";")

        for value in list_of_entries:
            value = value.split(",")
            is_valid = value[3] == "" and value[4] == "" and value[5] == "" and value[6] == "" and value[11] == "" and value[12] == "" and value[13] == "" and is_valid

        is_valid_dict[key] = is_valid_dict[key] and is_valid

    return is_valid_dict


def test_valid_hour_types(_: dict, cleaned_hours_dict: dict, is_valid_dict: dict) -> dict:
    """
    """
    for key, value in cleaned_hours_dict.items():
        is_valid = True
        list_of_entries = value.split(";")

        for value in list_of_entries:
            value = value.split(",")
            is_valid = value[10] in HOUR_TYPES and is_valid

        is_valid_dict[key] = is_valid_dict[key] and is_valid

    return is_valid_dict



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

    # REMOVE THIS SECTION AFTER DONE TESTING:
    for key, value in cleaned_hours_dict.items():
        print(cleaned_hours_dict[key].split(";"))

    # # Test OAI Hours 
    is_valid_hours_dict = test_day_of_month_formatting(id_hours_dict, cleaned_hours_dict, is_valid_hours_dict)
    is_valid_hours_dict = test_valid_day_of_week(id_hours_dict, cleaned_hours_dict, is_valid_hours_dict)
    is_valid_hours_dict = test_valid_entry_format(id_hours_dict, cleaned_hours_dict, is_valid_hours_dict)
    is_valid_hours_dict = test_valid_open_closed_hours(id_hours_dict, cleaned_hours_dict, is_valid_hours_dict)
    is_valid_hours_dict = test_week_of_month_formatting(id_hours_dict, cleaned_hours_dict, is_valid_hours_dict)
    is_valid_hours_dict = test_close_hour_greater_than_open_hour(id_hours_dict, cleaned_hours_dict, is_valid_hours_dict)
    is_valid_hours_dict = test_weekly_formatting(id_hours_dict, cleaned_hours_dict, is_valid_hours_dict)
    is_valid_hours_dict = test_all_null_values_empty_string(id_hours_dict, cleaned_hours_dict, is_valid_hours_dict)
    print(is_valid_hours_dict)

    # Check Values Still Valid
    valid_id_hours_dict = filter_invalid_values(id_hours_dict, cleaned_hours_dict, is_valid_hours_dict)

    # Convert Back to DF
    cleaned_hours_df = convert_id_hours_dict_to_df(cleaned_hours_dict, is_valid_hours_dict, df)