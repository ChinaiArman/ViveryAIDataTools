<!-- LINK TO TOP -->
<a name="readme-top"></a>



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/ChinaiArman/ViveryAIDataCleanser">
    <img src="logo.png" alt="Logo" width="200">
  </a>
  <h3 align="center">Vivery AI Data Cleanser</h3>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#about-vivery">About Vivery</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#installation">Installation</a></li>
        <li><a href="#usage">Usage</a></li>
        <li><a href="#common-bug-fixes">Common Bug Fixes</a></li>
      </ul>
    </li>
    <li><a href="#update-history">Update History</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

Vivery’s Artificial Intelligence Data Cleanser represents the companies first step into the AI era of technology. The AI Data Cleanser uses a **fine-tuned OpenAI model** to parse pantry operational hours into formatted, data-base ready entries. 

Previously, networks submit their hours in plain English, requiring a translation to turn the plaintext hours into hours in the databases format. This was a manual process previously, as there is no algorithmic approach for language processing. Each network can share their hours in a unique, completely unformatted way. Translating these hours to the database format could take up to multiple days to complete. 

The AI Data Cleanser reduced this lengthy task down to just a few minutes of run time. The model was trained on a large set of previously cleaned hours, and then supported with comprehensive testing to ensure the outputs generated are valid.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ABOUT VIVERY -->
## About Vivery
Vivery is a digital **network of food banks and pantries across America**, enabling the people they serve to connect together on one centralized platform. The Vivery network equalizes access so neighbors (people struggling with hunger or homelessness) can easily **find the right food, programs and services nearby.** As an American non-profit, Vivery simultaneously provides a tech boost to these food banks at no cost, allowing them to **focus on serving their communities.** For more information, visit https://www.vivery.org/. 

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

Below are a set of instructions that will walk you through setting up this repository. The instructions are written for the **Windows Operating system**, but should be near identical for the Mac OS. The only prerequisites are to **have Python installed on your machine and a bulk upload file to analyze.** 

### Installation

1. Clone this repository
   ```sh
   git clone https://github.com/ChinaiArman/ViveryAIDataCleanser.git
   ```
2. Install packages
   ```sh
   pip install -r requirements.txt
   ```
3. Adding an API Key
    1. Create a file within the repository called `keys.py`.
    2. Insert the following code within the `keys.py` file. Note that an API key must be granted by an Administrator in the OpenAI portal.
        ```python
        NORTH_CENTRAL_API_KEY = {
            "key": "<YOUR API KEY HERE>",
            "base": "https://vivery-ai-training.openai.azure.com/",
            "engine": "cleanse-hours"
        }
        ```

### Usage
4. For the python script to run successfully, **the following columns must be present within the file.** All other columns and their values will be transferred over to the output file after execution.
    - Program External ID
        - **CANNOT** be null
        - **MUST** be unique
    - Hours Day of Week
    - Hours Open 1
    - Hours Open 2
    - Hours Closed 2
    - Hours Open 3
    - Hours Note
    - Hours Week of Month
    - Hours Day of Month
    - Hours Specific Date
    - Hours Specific Date Closed Indicator
    - Hours Specific Date Reason
5. After ensuring all of the columns are present, **a new column must be created.** This column must be given the name ``Hours Uncleaned``. This column will hold all of the uncleaned hour entries. All entries for the program **must fit within this single cell as a plaintext string.** 
6. **Save** this file, then move it to the working directory.
    - This file can either be stored at the same level as the ``clean_hours.py`` script, or within a subfolder named *csv*. The *csv* folder will be created upon running the ``clean_hours.py`` script for the first time.
7. Create a new terminal within the working directory and run the following command:
    ```sh
    python clean_hours.py "<PATH TO BULK UPLOAD FILE>"
    ```
This command will run the cleansing script on the prepared Bulk Upload File. Both the input and the output file will be saved in the csv folder. The script can take several minutes to run depending on the length of the file. The progress of the script can be monitored within the terminal.

### Common Bug Fixes
- This is a place where errors that arise during the execution of the script can be documented, along with their solutions


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- UPDATE HISTORY -->
## Update History

- ``October 1, 2023 --> Begin initial development``
- ``December 1, 2023 --> Release version 1.1.0``

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

For questions about this repository and the files inside, please direct emails to arman@vivery.org, with `Vivery AI Data Cleanser` contained within the subject line.

[![Linkedin](https://img.shields.io/badge/linkedin-%230077B5.svg?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/armanchinai/)
&nbsp;
[![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)](https://github.com/ChinaiArman)

<p align="right">(<a href="#readme-top">back to top</a>)</p>