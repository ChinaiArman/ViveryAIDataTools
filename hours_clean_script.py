"""
"""


# PACKAGE IMPORTS
import openai

# LOCAL FILE IMPORTS


# IMPORT CONSTANTS
from keys import API_KEY

#MISC CONSTANTS





# HELPERS





# MAIN
if __name__ == "__main__": 
    openai.api_type = "azure"
    openai.api_base = "https://viveryadvocate.openai.azure.com/"
    openai.api_version = "2022-12-01"
    openai.api_key = API_KEY

    response = openai.Completion.create(
    engine="arman_hours_clean_model",
    prompt="Q: Mon-Fri,10:00:00 AM,4:00:00 PM\nA:",
    temperature=0.2,
    max_tokens=100,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    best_of=1,
    stop=["%%"])

    print(response)