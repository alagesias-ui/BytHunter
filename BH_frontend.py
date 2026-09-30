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

#%%
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

# CREATE DATAFRAME

# TRANSOFORM DATAFRAME

# CREATE FRONTEND STREAMLIT APP

# %%
