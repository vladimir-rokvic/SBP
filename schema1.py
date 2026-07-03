from pymongo import MongoClient
import pandas as pd
from tqdm import tqdm
import math

numeric_cols = [
    'Calcium, Ca-MG',
    'Carbohydrate, by difference-G', 'Cholesterol-MG', 'Copper, Cu-MG',
    'Energy-KCAL', 'Fatty acids, total monounsaturated-G',
    'Fatty acids, total polyunsaturated-G',
    'Fatty acids, total saturated-G', 'Fatty acids, total trans-G',
    'Fiber, soluble-G', 'Fiber, total dietary-G', 'Folate, total-UG',
    'Folic acid-UG', 'Iron, Fe-MG', 'Magnesium, Mg-MG', 'Manganese, Mn-MG',
    'Niacin-MG', 'Pantothenic acid-MG', 'Phosphorus, P-MG',
    'Potassium, K-MG', 'Protein-G', 'Riboflavin-MG', 'Sodium, Na-MG',
    'Sugars, added-G', 'Sugars, total including NLEA-G', 'Thiamin-MG',
    'Total lipid (fat)-G', 'Total sugar alcohols-G', 'Vitamin A, IU-IU',
    'Vitamin B-12-UG', 'Vitamin B-6-MG',
    'Vitamin C, total ascorbic acid-MG',
    'Vitamin D (D2 + D3), International Units-IU', 'Vitamin D (D2 + D3)-UG',
    'Zinc, Zn-MG'
]

date_cols = ['modified_date', 'available_date']

numeric_cols_set = set(numeric_cols)


def clean_row(row):
    for col, val in row.items():
        if val is None or (isinstance(val, float) and math.isnan(val)):
            row[col] = 0 if col in numeric_cols_set else None
    return row


df = pd.read_csv("fda_approved_food_items_w_nutrient_info.csv",
                 dtype={"gtin_upc": str})
df = df.dropna(subset=["brand_owner"])

client = MongoClient("mongodb://localhost:27017/")
mydb = client["projectdb"]
products_col = mydb["products"]
owners_col = mydb["owners"]

products_col.drop()
owners_col.drop()

owner_stats = df.groupby("brand_owner").agg(
    product_count=("fdc_id", "count"),
    category_count=("branded_food_category", "nunique")
).reset_index()

owner_docs = {}
owner_records = [
    {"name": row["brand_owner"], "product_count": row["product_count"],
     "category_count": row["category_count"]}
    for _, row in owner_stats.iterrows()
]
result = owners_col.insert_many(owner_records)
for i, owner_name in enumerate(owner_stats["brand_owner"]):
    owner_docs[owner_name] = result.inserted_ids[i]

rows = df.to_dict(orient="records")
for row in tqdm(rows, desc="Preparing products"):
    row = clean_row(row)
    row["owner"] = owner_docs[row["brand_owner"]]
    del row["brand_owner"]

BATCH_SIZE = 10_000
for i in tqdm(range(0, len(rows), BATCH_SIZE), desc="Inserting products"):
    products_col.insert_many(rows[i:i + BATCH_SIZE])

print(client.list_database_names())
print(mydb.list_collection_names())
