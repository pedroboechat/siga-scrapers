"""Scraper for SIGA open courses page"""

# Imports
## Standard libraries
import csv
## Other libraries
from bs4 import BeautifulSoup as bs
import pandas as pd
import requests

# Get all `curriculum` pages links
BASE_URL = "https://siga.ufrj.br/sira/gradeHoraria/"
with open("./COURSE.conf", encoding="utf-8") as conf:
    COURSE_ID = conf.readlines()[0].strip()
open_courses_soup = bs(
    requests.get(
        BASE_URL +
        COURSE_ID.replace(".html", "") +
        ".html"
    ).text,
    "html.parser"
)
COLUMNS = [
    "periodo",
    "codigo",
    "turma",
    "disciplina",
    "dia",
    "horario",
    "docentes"
]

# Extract `open courses` page data
## Initialize DataFrame
df = pd.DataFrame(
    columns=[
        "Período",
        "Código",
        "Turma",
        "Nome Turma",
        "Dia",
        "Horário",
        "Professor"
    ]
)

## Load HTML tables as DataFrames
tables_list = pd.read_html(str(open_courses_soup), header=0)

## Create semester dictionary
semester_dict = dict()
for index in range(len(tables_list)):
    if tables_list[index].columns[0].endswith("Período"):
        semester_dict[tables_list[index].columns[0]] = index
        continue
    if "Lista de Disciplinas Complementares" in tables_list[index].columns:
        try:
            if len(tables_list[index+3]):
                semester_dict["Complementares"] = index+2
                continue
        except KeyError:
            pass

## Loop extracting semester `table` data
for semester_key, semester_value in semester_dict.items():
    semester_df = tables_list[semester_value+1].fillna(method="ffill")
    semester_df["Período"] = semester_key
    df = pd.concat(
        [
            df,
            semester_df
        ],
        join="inner",
        ignore_index=True
    )

# Data treatment
## Rename columns
df.columns = COLUMNS
## Change `turma` column dtype
df["turma"] = df["turma"].astype(int)

# Export DataFrame
df.to_excel(
    f"./open_courses.xlsx",
    index=False
)
df.to_csv(
    f"./open_courses.zip",
    sep=";",
    index=False,
    compression={
        "method": "zip",
        "archive_name": f"open_courses.csv"
    },
    quoting=csv.QUOTE_ALL
)
