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
columns = ['subtype', 'price', 'pricePerSqm', 'usableArea', 'city', 'street', 'poiSchoolDistance', 'poiBusDistance','detailUrl']
df_clean = df[columns].copy()
df_clean.rename(columns={
    'subtype': 'Layout',
    'price': 'Price',
    'pricePerSqm': 'Price per m2',
    'usableArea': 'Usable Area (m2)',
    'city': 'City',
    'street':'Street',
    'poiSchoolDistance': 'Distance to School (m)', 'poiBusDistance': 'Distance to Bus Stop (m)',
    'detailUrl': 'Link',
    }, inplace=True)
df_clean['Street'] = df_clean['Street'].fillna(df_clean['City']) # U menších obcích se neobjevují názvy ulic, proto se do sloupce Street doplní název města.
df_clean['Price'] = df_clean['Price']/1000000
df_clean.head()

# VARIABLES
count_rows = df_clean.shape[0]
mean_cena = round(df_clean['Price'].mean())
max_cena = round(df_clean['Price'].max())
min_cena = round(df_clean['Price'].min())
mean_cena_m2 = round(df_clean['Price per m2'].mean())
max_cena_m2 = round(df_clean['Price per m2'].max())
min_cena_m2 = round(df_clean['Price per m2'].min())

df['scrapedAt'] = pd.to_datetime(df['scrapedAt'])
max_scraped_at = df['scrapedAt'].max()
posledni_update = max_scraped_at.strftime("%d.%m.%Y v %H:%M")


# MOST EXPENSIVE CITY
# Nejdražší město na cenu m2
max_cena_m2_město = (
    df_clean.groupby("City", as_index=False)["Price per m2"]
    .mean()
    .sort_values(by=["Price per m2"], ascending=False)["City"]
    .iloc[0]
) 

# Počet nabídek na nejdražší město
max_cena_m2_počet_nabídek = df_clean[df_clean['City'] == max_cena_m2_město].shape[0] 

# Cena bytu v nejdražším městě
max_cena_m2_hodnota = int(
    round(df_clean[df_clean["City"] == max_cena_m2_město]["Price per m2"].mean())
)

# MAIN CITY IN SOUTHERN BOHEMIA
mean_cena_budějovice = round(df_clean[df_clean['City'] == "České Budějovice"]["Price per m2"].mean())
budějovice_počet_nabídek = df_clean[df_clean['City'] == "České Budějovice"].shape[0]

# STREAMLIT APP

# INTRO
st.title('BytHunter | Real Estate Aggregator for South Bohemia')
st.header('Intro', divider='rainbow')
st.markdown("""
BytHunter aggregates real estate information in South Bohemia from various sources and provides it to the application. The application allows users to search for and view property information available across different sources.
\n In addition, the application allows content personalization based on region, price, or distance to a transit stop or school.
""")

# ABSTRACT
st.header('Basic Overview', divider='rainbow')
st.markdown(f"""
The application displays a total of **{count_rows}** properties in South Bohemia. Prices per square meter range from **{min_cena_m2}** to **{max_cena_m2}** CZK. The most expensive city is **{max_cena_m2_město}**, which offers **{max_cena_m2_počet_nabídek}** listings at an average price of **{max_cena_m2_hodnota}** CZK.
\n The most searched city, České Budějovice, currently offers **{budějovice_počet_nabídek}** listings for apartments at an average price of **{mean_cena_budějovice}** CZK.
""")

# TABLE
st.caption(f"🕒 **Last updated:** {posledni_update}")
st.dataframe(
    df_clean,
    column_config={
        "Price": st.column_config.NumberColumn(
                    "Price", format="%.2f mil Kč"
                ),
        "Price per m2": st.column_config.NumberColumn(
            "Price per m2", format="%,d Kč/m²"
        ),
        "Usable Area (m2)": st.column_config.NumberColumn(
            "Usable Area (m²)", format="%d m²"
        ),
        "Link": st.column_config.LinkColumn(
                    "Link",                     # Název sloupce v tabulce
                    display_text="Otevřít 🔗",  # Co se zobrazí místo té dlouhé URL (volitelné)
                    width="small"
                ),
    },
    hide_index=True,  # Schová zbytečný číselný index vlevo
)
