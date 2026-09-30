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

# GET API DATA
client = ApifyClient("apify_api_ACPNPpWucTeqdmh9oWYQahu4tDzXJk1S5dSx")
run_input = {
    "regionIds": ["1"],
    "transaction": "sale",  # Prodej
    "category": "apartment",  # Byty
    "subtypeCodes": ["6","7"],
    "priceMin": 4500000,
    "priceMax": 7500000,
    "usableAreaMin": 60,
    "usableAreaMax": 120,
    "sort": "newest",
    "maxListings": 100,
    "proxyConfiguration": {"useApifyProxy": True},
}

# SPUŠTĚNÍ ACTORA
print("Spouštím scraping Srealit...")
run = client.actor("logiover/sreality-cz-scraper-czech-real-estate-data").call(run_input=run_input)

# NAČTENÍ DAT
dataset_items = client.dataset(run.default_dataset_id).list_items().items
df = pd.DataFrame(dataset_items)

# ZÁPIS DAT DO POSTGRESQL
if not df.empty:
  try:
    print("Zapisuji data do databáze...")

    # Zápis do tabulky "nemovitosti"
    df.to_sql(
        name="nemovitosti",
        con=engine,
        if_exists="replace",  # Options: 'append' (přidá řádky), 'replace' (přepíše tabulku), 'fail' (vyhodí chybu pokud existuje)
        index=False,  # Nezapisovat pandas index jako samostatný sloupec
        method="multi",  # Zrychlí vkládání více řádků
    )

    print("Data byla úspěšně zapsána do tabulky 'nemovitosti'!")
    st.success("Data byla úspěšně uložena do databáze!")

  except Exception as e:
    print(f"Chyba při zápisu do databáze: {e}")
    st.error(f"Chyba při zápisu do databáze: {e}")
else:
  print("DataFrame je prázdný, žádná data k zápisu.")
  st.warning("Scraper nevrátil žádná data.")