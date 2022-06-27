# Imports
## Standard libraries
import csv

## Other libraries
from bs4 import BeautifulSoup as bs
import pandas as pd
import requests
from tqdm import tqdm

# Get all `curriculum` pages links
BASE_URL = "https://siga.ufrj.br/sira/repositorio-curriculo/disciplinas/"
all_subjects_soup = bs(
    requests.get(
        BASE_URL
    ).text,
    "html.parser"
)
COLUMNS = [
    "codigo",
    "disciplina",
    "ementa"
]

# Extract `courses subjects` page data
## Definition of helper functions
def subject_parser(soup: bs) -> pd.DataFrame:
    """Parses a SIGA course subject page and returns its data as a DataFrame

    Args:
        soup (bs): Soup of the SIGA course subject page to be parsed

    Returns:
        DataFrame: Parsed table as DataFrame
    """
    all_tds = soup.find("table", class_="cellspacingTable").findAll("td")
    try:
        code_and_course = all_tds[0].get_text()
        code_course_sep_index = code_and_course.find("-")
        code = code_and_course[:code_course_sep_index]
        course = code_and_course[code_course_sep_index+1:]
        subject = all_tds[1].get_text()
    except:
        print(all_tds)
        raise
    return pd.DataFrame(
        [(
            code.strip(),
            course.strip(),
            subject.strip()
        )],
        columns=COLUMNS
    )

## Initialize DataFrame
df = pd.DataFrame()

## Get all courses subjects pages soups
subject_hrefs = list(map(
    lambda x: BASE_URL+x,
    pd.read_html(
        str(all_subjects_soup)
    )[0]["Name"].dropna().iloc[1:].to_list()
))
subject_reqs = list()
for subject_href in subject_hrefs:
    subject_reqs.append(
        requests.get(subject_href).text
    )
subject_soups = list(map(lambda x: bs(x), subject_reqs))

## Loop extracting course subject data
for subject_soup in tqdm(subject_soups):
    df = pd.concat([
        df,
        subject_parser(subject_soup)
    ])

# Export DataFrame
df.to_excel(
    "./courses_subjects.xlsx",
    index=False
)
df.to_csv(
    "./courses_subjects.zip",
    sep=";",
    index=False,
    compression={
        "method": "zip",
        "archive_name": "courses_subjects.csv"
    },
    quoting=csv.QUOTE_ALL
)
