# IMPORT LIBRARIES
import os
import pandas as pd
from sqlalchemy import create_engine
from apify_client import ApifyClient
from dotenv import load_dotenv

# ENVIRONMENT VARIABLES
load_dotenv() # Načítá proměnné prostředí z .env souboru
DATABASE_URL = os.getenv("DATABASE_URL")
APIFY_TOKEN = os.getenv("APIFY_TOKEN")

if not DATABASE_URL or not APIFY_TOKEN:
    print("❌CHYBA: Chybí DATABASE_URL nebo APIFY_TOKEN v .env souboru!")
    exit()

engine_url = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1).replace("postgres://", "postgresql+psycopg2://", 1)
engine = create_engine(engine_url)

try:
    with engine.connect() as conn:
        print("✅Úspěšně připojeno k Neon.tech databázi přes SQLAlchemy!")
except Exception as e:
    print(f"❌Chyba při připojení k DB: {e}")
    exit()

# CALL API
client = ApifyClient(APIFY_TOKEN)
run_input = {
    "location": "České Budějovice",
    "maxProperties": 200,
    "offerType": ["PRODEJ"],
    "estateType": ["BYT", "DUM"],
    "priceFrom": 5000000,
    "priceTo": 7800000,
}

print("Spouštím scraping Bezrealitky...")
run = client.actor("real1ty/bezrealitky").call(run_input=run_input)

# ASSIGN DATAFRAME
dataset_items = client.dataset(run.default_dataset_id).list_items().items
df = pd.DataFrame(dataset_items)

# WRITE TO HISTORICAL DATABASE (APPEND)
if not df.empty:
    try:
        print("Zapisuji data do historické databáze...")
        df["scrapedAt"] = pd.Timestamp.now()
        df.to_sql(
            name="bz_nemovitosti_hist",
            con=engine,
            if_exists="append",
            index=False,
            method="multi",
        )
        print("✅Data byla úspěšně zapsána do tabulky 'bz_nemovitosti_hist'!")
    except Exception as e:
        print(f"❌Chyba při zápisu do historické databáze: {e}")
else:
    print("❌DataFrame je prázdný, žádná data k zápisu do historické databáze.")

# WRITE TO MAIN DATABASE (REPLACE)
if not df.empty:
    try:
        print("Zapisuji data do databáze...")
        df["scrapedAt"] = pd.Timestamp.now()
        df.to_sql(
            name="bz_nemovitosti",
            con=engine,
            if_exists="replace",
            index=False,
            method="multi",
        )
        print("✅Data byla úspěšně zapsána do tabulky 'bz_nemovitosti'!")
    except Exception as e:
        print(f"❌Chyba při zápisu do databáze: {e}")
else:
    print("❌DataFrame je prázdný, žádná data k zápisu do main databáze.")