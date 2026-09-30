# IMPORT LIBRARIES
import streamlit as st
import pandas as pd
import numpy as np
import os
import altair as alt
import psycopg2
from pathlib import Path
from psycopg2.extras import execute_values
from sqlalchemy import create_engine
from apify_client import ApifyClient

# POSTGRESQL LOGIN
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "159753")

try:
    # 2. Vytvoření síťového spojení do databáze
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        connect_timeout=5,
    )

    # 3. Vytvoření cursoru (vykonavatele příkazů)
    cur = conn.cursor()

    # 4. Testovací dotaz na ověření spojení (zjistí verzi PostgreSQL)
    cur.execute("SELECT version();")
    db_version = cur.fetchone()

    print("Úspěšně připojeno k PostgreSQL databázi!")
    print(f"Verze DB: {db_version[0]}")

except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.stop()

# DB QUERY
engine = create_engine(f'postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

# SET UP PANDAS RULES
pd.set_option("display.max_columns", None) # Metody budou zobrazovat všechny sloupce
pd.set_option("display.max_colwidth", None) # Maximální šířka sloupce bude neomezená
pd.set_option("display.width", 1000)

# QUERY POSTGRESQL DATABASE
df = pd.read_sql_query("SELECT * FROM nemovitosti", engine)

# TRANSFORM DATAFRAME
columns = ['adId', 'subtype', 'price', 'pricePerSqm', 'usableArea', 'city', 'street', 'poiSchoolDistance', 'poiBusDistance','detailUrl']
df_clean = df[columns].copy()
df_clean.rename(columns={
    'adId': 'Index',
    'subtype': 'Dispozice',
    'price': 'Cena',
    'pricePerSqm': 'Cena m2',
    'usableArea': 'Výměra (m2)',
    'city': 'Město',
    'street':'Ulice',
    'poiSchoolDistance': 'Vz. od školy (m)', 'poiBusDistance': 'Vz. od zastávky (m)',
    'detailUrl': 'Odkaz'
    }, inplace=True)
df_clean.head()

# VARIABLES
count_rows = df_clean.shape[0]
mean_cena = round(df_clean['Cena'].mean())
max_cena = round(df_clean['Cena'].max())
min_cena = round(df_clean['Cena'].min())
mean_cena_m2 = round(df_clean['Cena m2'].mean())
max_cena_m2 = round(df_clean['Cena m2'].max())
min_cena_m2 = round(df_clean['Cena m2'].min())

# MOST EXPENSIVE CITY
# Nejdražší město na cenu m2
max_cena_m2_město = (
    df_clean.groupby("Město", as_index=False)["Cena m2"]
    .mean()
    .sort_values(by=["Cena m2"], ascending=False)["Město"]
    .iloc[0]
) 

# Počet nabídek na nejdražší město
max_cena_m2_počet_nabídek = df_clean[df_clean['Město'] == max_cena_m2_město].shape[0] 

# Cena bytu v nejdražším městě
max_cena_m2_hodnota = int(
    round(df_clean[df_clean["Město"] == max_cena_m2_město]["Cena m2"].mean())
)

# STREAMLIT APP
st.title('BytHunter | Agregátor nemovitostí')
st.header('Úvod', divider='rainbow')
st.markdown("""
BytHunter agreguje informace o nemovitostech v jižních čechách z různých zdrojů a poskytuje je do aplikace. Aplikace umožňuje vyhledávat a zobrazovat informace o nemovitostech, které jsou dostupné v různých zdrojích.
\n Aplikace navíc umožňuje obsah personalizovat podle oblasti, ceny, nebo vzdálenosti od zastávky nebo školy.
""")
st.header('Základní přehled', divider='rainbow')
st.markdown(f"""
Aplikace zobrazuje celkem **{count_rows}** nemovitostí v jižních čechách. Ceny za metr čtvereční se pohybují od **{min_cena_m2}** do **{max_cena_m2}** Kč. Nejdražším městem je **{max_cena_m2_město}**, které za cenu bytu **{max_cena_m2_hodnota}** Kč nabízí **{max_cena_m2_počet_nabídek}** nabídek.
""")
