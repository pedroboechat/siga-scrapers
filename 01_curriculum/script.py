"""Scraper for SIGA curriculum page"""

# Imports
## Standard libraries
import csv
import re

## Other libraries
from bs4 import BeautifulSoup as bs
import numpy as np
import pandas as pd
import requests

# Get all `curriculum` pages links
BASE_URL = "https://siga.ufrj.br/sira/repositorio-curriculo/distribuicoes/"
with open("./CURRICULUM-ID.conf", encoding="utf-8") as conf:
    CURRICULUM_ID = conf.readlines()[0].strip()

curriculum_soup = bs(
    requests.get(
        BASE_URL +
        CURRICULUM_ID.replace(".html", "") +
        ".html"
    ).text,
    "html.parser"
)

COLUMNS = [
    "curso",
    "periodo",
    "codigo",
    "disciplina",
    "ementa",
    "creditos",
    "ch_teorica",
    "ch_pratica",
    "ch_extensao",
    "requisitos"
]

# Extract `curriculum` page data
## Definition of helper functions
def table_parser(table: bs) -> pd.DataFrame:
    """Parses a SIGA table and returns its data as a DataFrame

    Args:
        table (BeautifulSoup): Soup of the table to be parsed

    Returns:
        DataFrame: Parsed table as DataFrame
    """
    try:
        semester = table.find("tr", class_="tableTitle").find("b").stripped_strings.__next__()
    except (AttributeError, StopIteration):
        return pd.DataFrame(
            columns=COLUMNS
        )
    if semester.startswith("Curso"):
        return pd.DataFrame(
            [(
                semester,
                np.NaN,
                np.NaN,
                np.NaN,
                np.NaN,
                np.NaN,
                np.NaN,
                np.NaN,
                np.NaN,
                np.NaN
            )],
            columns=COLUMNS
        )
    elif (
        "Período" in semester or
        "Escolha Condicionada" in semester or
        "Escolha Restrita" in semester
    ):
        courses_list = []
        if "Escolha Condicionada" in semester:
            semester = "Escolha Condicionada"
        if "Escolha Restrita" in semester:
            semester = "Grupo Humanas"
            rows = table.find("b", string="Grupo Humanas").find_all_next("tr")
        else:
            rows = table.find_all("tr")[2:]
        for row in rows:
            cols = row.find_all("td")
            try:
                code = cols[0].stripped_strings.__next__()
                if "Atividades" in code or "Total de" in code:
                    break
                subject_href = cols[0].find("a").get("href")
            except (AttributeError, StopIteration):
                break
            subject = bs(
                    requests.get(
                        BASE_URL + subject_href[
                            subject_href.find("(")+2:subject_href.find(")")-1
                        ]
                    ).text,
                    "html.parser"
                ).find(
                    "table",
                    class_="cellspacingTable"
                ).find_all(
                    "tr"
                )[1].find(
                    "td"
                ).stripped_strings.__next__()
            course = cols[1].stripped_strings.__next__()
            creds = cols[2].stripped_strings.__next__()
            teorical_hours = cols[3].stripped_strings.__next__()
            practical_hours = cols[4].stripped_strings.__next__()
            extension_hours = cols[5].stripped_strings.__next__()
            requirements = re.sub(
                    r"^.*=.*$",
                    "",
                    cols[6].get_text().strip()
                ).replace(
                    "\n",
                    ","
                ).split(",")
            courses_list.append(
                (
                    np.NaN,
                    semester,
                    code,
                    course,
                    subject,
                    creds,
                    teorical_hours,
                    practical_hours,
                    extension_hours,
                    requirements
                )
            )
        return pd.DataFrame(
            courses_list,
            columns=COLUMNS
        )
    else:
        return pd.DataFrame(
            columns=COLUMNS
        )

# Initialize DataFrame
df = pd.DataFrame()

# Loop through the `soup` extracting semester `table` data
for table_soup in curriculum_soup.find_all("table", class_="cellspacingTable"):
    df = pd.concat([
        df,
        table_parser(table_soup)
    ])

# Data treatment
## Fill `curso` column
df["curso"] = df["curso"].fillna(method="ffill")

## Drop first row (that only holds `curso` data)
df = df.drop(0)

## Reset DataFrame index
df = df.reset_index(drop=True)

# Export DataFrame
grad = df["curso"].iloc[0].lower().replace("curso de graduação em ", "").replace(" ", "_")

df.to_excel(
    f"./curriculum_{grad}.xlsx",
    index=False
)

df.to_csv(
    f"./curriculum_{grad}.zip",
    sep=";",
    index=False,
    compression={
        "method": "zip",
        "archive_name": f"curriculum_{grad}.csv"
    },
    quoting=csv.QUOTE_ALL
)
