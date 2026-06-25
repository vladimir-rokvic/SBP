from pymongo import MongoClient
import pandas as pd
from tqdm import tqdm

df = pd.read_csv("fda_approved_food_items_w_nutrient_info.csv", dtype={"gtin_upc": str})
df = df.dropna(subset=["brand_owner"])

client = MongoClient("mongodb://localhost:27017/")
mydb = client["projectdb"]
products_col = mydb["products"]
owners_col = mydb["owners"]

products_col.drop()  # ← clear before re-running
owners_col.drop()

# Compute all owner stats in one pass instead of filtering per owner
owner_stats = df.groupby("brand_owner").agg(
    product_count=("fdc_id", "count"),
    category_count=("branded_food_category", "nunique")
).reset_index()

owner_docs = {}
owner_records = [
    {"name": row["brand_owner"], "product_count": row["product_count"], "category_count": row["category_count"]}
    for _, row in owner_stats.iterrows()
]
result = owners_col.insert_many(owner_records)
for i, owner_name in enumerate(owner_stats["brand_owner"]):
    owner_docs[owner_name] = result.inserted_ids[i]

rows = df.to_dict(orient="records")
for row in tqdm(rows, desc="Preparing products"):
    row["owner"] = owner_docs[row["brand_owner"]]
    del row["brand_owner"]

# Insert in batches to avoid memory issues with 1.8M docs
BATCH_SIZE = 10_000
for i in tqdm(range(0, len(rows), BATCH_SIZE), desc="Inserting products"):
    products_col.insert_many(rows[i:i + BATCH_SIZE])

print(client.list_database_names())
print(mydb.list_collection_names())
