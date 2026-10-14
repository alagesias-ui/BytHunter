# IMPORT LIBRARIES
import json
import os
from apify_client import ApifyClient
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine

# ENVIRONMENT VARIABLES
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
APIFY_TOKEN = os.getenv("APIFY_TOKEN")

if not DATABASE_URL or not APIFY_TOKEN:
  print("❌ CHYBA: Chybí DATABASE_URL nebo APIFY_TOKEN v .env souboru!")
  exit()

# PostgreSQL Connection Engine Setup
engine_url = (
    DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
    .replace("postgres://", "postgresql+psycopg2://", 1)
)
engine = create_engine(engine_url)

try:
  with engine.connect() as conn:
    print("✅ Úspěšně připojeno k Neon.tech databázi přes SQLAlchemy!")
except Exception as e:
  print(f"❌ Chyba při připojení k DB: {e}")
  exit()

# CALL API
client = ApifyClient(APIFY_TOKEN)
locations = ["České Budějovice", "Český Krumlov"]
all_dfs = []

for loc in locations:
  print(f"Spouštím scraping Bezrealitky pro lokalitu: {loc}...")
  run_input = {
      "location": loc,  # String pro dané město
      "maxProperties": 200,
      "offerType": ["PRODEJ"],
      "estateType": ["BYT", "DUM"],
      "priceFrom": 5000000,
      "priceTo": 7800000,
  }

  run = client.actor("real1ty/bezrealitky").call(run_input=run_input)
  dataset_items = client.dataset(run.default_dataset_id).list_items().items

  if dataset_items:
    df_loc = pd.DataFrame(dataset_items)
    # Vložení sloupce city přímo pro aktuální město ve smyčce
    df_loc["city"] = loc
    all_dfs.append(df_loc)

# Spojení výsledků z obou měst do jednoho DataFrame
if all_dfs:
  df = pd.concat(all_dfs, ignore_index=True)
else:
  df = pd.DataFrame()

if not df.empty:
  # 1. Přidání času scrapování
  df["scrapedAt"] = pd.Timestamp.now()

  # 2. Extrakce ulice ze sloupce address (vezme text před první čárkou)
  if "address" in df.columns:
    df["street"] = df["address"].astype(str).str.split(",").str[0].str.strip()
  else:
    df["street"] = None

  # 3. Explicitní serializace vnořených objektů (dicts) a polí (lists) na JSON stringy
  json_columns = [
      "coordinates",
      "mortgageData",
      "mainImage",
      "publicImages",
      "videos",
      "links",
      "tags",
      "project",
      "nemoreport",
  ]

  for col in json_columns:
    if col in df.columns:
      df[col] = df[col].apply(
          lambda x: json.dumps(x)
          if x is not None and not (isinstance(x, float) and pd.isna(x))
          else None
      )

  # 4. ZÁPIS DO HISTORICKÉ DATABÁZE (APPEND)
  try:
    print("Zapisuji data do historické tabulky (bz_nemovitosti_hist)...")
    df.to_sql(
        name="bz_nemovitosti_hist",
        con=engine,
        if_exists="append",
        index=False,
        method="multi",
    )
    print("✅ Data byla úspěšně zapsána do 'bz_nemovitosti_hist'!")
  except Exception as e:
    print(f"❌ Chyba při zápisu do historické databáze: {e}")

  # 5. ZÁPIS DO HLAVNÍ DATABÁZE (REPLACE)
  try:
    print("Zapisuji data do hlavní tabulky (bz_nemovitosti)...")
    df.to_sql(
        name="bz_nemovitosti",
        con=engine,
        if_exists="replace",
        index=False,
        method="multi",
    )
    print("✅ Data byla úspěšně zapsána do 'bz_nemovitosti'!")
  except Exception as e:
    print(f"❌ Chyba při zápisu do hlavní databáze: {e}")
else:
  print("❌ DataFrame je prázdný, žádná data k zápisu.")