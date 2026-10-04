# IMPORT LIBRARIES
import streamlit as st
import pandas as pd
import numpy as np
import os
import altair as alt
import psycopg2
from pathlib import Path
from sqlalchemy import create_engine
from dotenv import load_dotenv

# ENVIRONMENT VARIABLES
load_dotenv() # Načítá proměnné prostředí z .env souboru
DATABASE_URL = os.getenv("DATABASE_URL")

engine_url = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1).replace("postgres://", "postgresql+psycopg2://", 1)
engine = create_engine(engine_url)

try:
    with engine.connect() as conn:
        print("Úspěšně připojeno k Neon.tech databázi přes SQLAlchemy!")
except Exception as e:
    print(f"❌Chyba při připojení k DB: {e}")
    exit()

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
    'pricePerSqm': 'Price per m²',
    'usableArea': 'Area (m²)',
    'city': 'City',
    'street':'Street',
    'poiSchoolDistance': 'Dis. to School (m)', 'poiBusDistance': 'Dis. to Bus Stop (m)',
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
mean_cena_m2 = round(df_clean['Price per m²'].mean())
max_cena_m2 = round(df_clean['Price per m²'].max())
min_cena_m2 = round(df_clean['Price per m²'].min())

df['scrapedAt'] = pd.to_datetime(df['scrapedAt'])
max_scraped_at = df['scrapedAt'].max()
posledni_update = max_scraped_at.strftime("%d.%m.%Y at %H:%M GMT+2")


# MOST EXPENSIVE CITY
# Nejdražší město na cenu m2
max_cena_m2_město = (
    df_clean.groupby("City", as_index=False)["Price per m²"]
    .mean()
    .sort_values(by=["Price per m²"], ascending=False)["City"]
    .iloc[0]
) 

# Počet nabídek na nejdražší město
max_cena_m2_počet_nabídek = df_clean[df_clean['City'] == max_cena_m2_město].shape[0] 

# Cena bytu v nejdražším městě
max_cena_m2_hodnota = int(
    round(df_clean[df_clean["City"] == max_cena_m2_město]["Price per m²"].mean())
)

# MAIN CITY IN SOUTHERN BOHEMIA
mean_cena_budějovice = round(df_clean[df_clean['City'] == "České Budějovice"]["Price per m²"].mean())
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
The application displays a total of **{count_rows}** properties in South Bohemia. Prices per square meter range from **{min_cena_m2}** to **{max_cena_m2}** CZK. The most expensive city on average is **{max_cena_m2_město}**, which offers **{max_cena_m2_počet_nabídek}** listings at an average price of **{max_cena_m2_hodnota}** CZK.
\n The regional capital city, České Budějovice, currently offers **{budějovice_počet_nabídek}** listings for apartments at an average price of **{mean_cena_budějovice}** CZK.
""")

# TABLE
st.caption(f"🕒 **Last updated:** {posledni_update}")
st.dataframe(
    df_clean,
    column_config={
        "Price": st.column_config.NumberColumn(
                    "Price", format="%.2f mil Kč"
                ),
        "Price per m²": st.column_config.NumberColumn(
            "Price per m²", format="%,d Kč/m²"
        ),
        "Area (m²)": st.column_config.NumberColumn(
            "Area (m²)", format="%d m²"
        ),
        "Link": st.column_config.LinkColumn(
                    "Link",                     # Název sloupce v tabulce
                    display_text="Otevřít 🔗",  # Co se zobrazí místo té dlouhé URL (volitelné)
                    width="small"
                ),
    },
    hide_index=True,  # Schová zbytečný číselný index vlevo
)
st.caption(f"🕒 **Source:** sreality.cz")