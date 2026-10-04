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
    "regionIds": ["1"],
    "transaction": "sale",
    "category": "apartment",
    "subtypeCodes": ["6", "7"],
    "priceMin": 5000000,
    "priceMax": 7500000,
    "usableAreaMin": 60,
    "usableAreaMax": 120,
    "sort": "newest",
    "maxListings": 200,
    "proxyConfiguration": {"useApifyProxy": True},
}

print("Spouštím scraping Srealit...")
run = client.actor("logiover/sreality-cz-scraper-czech-real-estate-data").call(run_input=run_input)

# ASSIGN DATAFRAME
dataset_items = client.dataset(run.default_dataset_id).list_items().items
df = pd.DataFrame(dataset_items)

# WRITE TO DATABASE
if not df.empty:
    try:
        print("Zapisuji data do databáze...")
        df["scrapedAt"] = pd.Timestamp.now()
        df.to_sql(
            name="nemovitosti",
            con=engine,
            if_exists="replace",
            index=False,
            method="multi",
        )
        print("Data byla úspěšně zapsána do tabulky 'nemovitosti'!")
    except Exception as e:
        print(f"Chyba při zápisu do databáze: {e}")
else:
    print("DataFrame je prázdný, žádná data k zápisu.")