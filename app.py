from pymongo import MongoClient
import pandas as pd
from tqdm import tqdm
from bson import ObjectId
import math
from datetime import datetime

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


def compute_nutri_score(row):
    unit = row.get("serving_size_unit", "")
    energy = row.get("Energy-KCAL", 0) or 0
    sugar = row.get("Sugars, total including NLEA-G", 0) or 0
    sodium = row.get("Sodium, Na-MG", 0) or 0
    sat_fat = row.get("Fatty acids, total saturated-G", 0) or 0
    trans_fat = row.get("Fatty acids, total trans-G", 0) or 0
    mono_fat = row.get("Fatty acids, total monounsaturated-G", 0) or 0
    poly_fat = row.get("Fatty acids, total polyunsaturated-G", 0) or 0
    fiber = row.get("Fiber, total dietary-G", 0) or 0
    protein = row.get("Protein-G", 0) or 0
    description = row.get("description") or ""
    ingredients = row.get("ingredients") or ""

    # Energy points
    if unit == "g":
        thresholds = [80, 160, 240, 320, 400, 480, 560, 640, 720, 800]
    else:
        thresholds = [7.2, 14.3, 21.5, 28.5, 35.9, 43.0, 50.2, 57.4, 64.5, 71.7]
    energy_points = next((i for i, t in enumerate(thresholds) if energy <= t), 10)

    # Sugar points
    if unit == "g":
        thresholds = [4.5, 9.0, 13.5, 18.0, 22.5, 27.0, 31.0, 36.0, 40.0, 45.0]
    else:
        thresholds = [0, 1.5, 3.0, 4.5, 6.0, 7.5, 9.0, 10.5, 12.5, 13.5]
    sugar_points = next((i for i, t in enumerate(thresholds) if sugar <= t), 10)

    # Salt points
    if unit == "g":
        thresholds = [90, 180, 270, 360, 450, 540, 630, 720, 810, 900]
        salt_points = next((i for i, t in enumerate(thresholds) if sodium <= t), 10)
    else:
        salt_points = 0

    # Fat points
    if unit == "g":
        thresholds = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        fat_points = next((i for i, t in enumerate(thresholds) if sat_fat <= t), 10)
    else:
        total_fat = sat_fat + trans_fat + mono_fat + poly_fat
        if total_fat == 0:
            ratio = 0
        else:
            ratio = sat_fat / total_fat
        thresholds = [0.1, 0.16, 0.22, 0.28, 0.34, 0.4, 0.46, 0.52, 0.58, 0.64]
        fat_points = next((i for i, t in enumerate(thresholds) if ratio <= t), 10)

    thresholds = [0.7, 1.4, 2.1, 2.8, 3.5]
    fiber_points = next((i for i, t in enumerate(thresholds) if fiber <= t), 5)

    thresholds = [1.6, 3.2, 4.8, 6.4, 8.0]
    protein_points = next((i for i, t in enumerate(thresholds) if protein <= t), 5)

    keywords_desc = ["vegetable", "fruit"]
    keywords_ing = ["carrot", "tomato", "cucumber", "berry"]
    fruit_veggie_points = 5 if (
        any(k in description.lower() for k in keywords_desc) or
        any(k in ingredients.lower() for k in keywords_ing)
    ) else 0

    positive = fiber_points + protein_points + fruit_veggie_points
    negative = energy_points + sugar_points + salt_points + fat_points
    final = negative - positive

    if final <= -1:
        grade = "A"
    elif final <= 2:
        grade = "B"
    elif final <= 10:
        grade = "C"
    elif final <= 18:
        grade = "D"
    else:
        grade = "E"

    return grade


def clean_row(row):
    for col, val in row.items():
        if val is None or (isinstance(val, float) and math.isnan(val)):
            row[col] = 0 if col in numeric_cols_set else None
    return row


def safe_parse(date_value):
    if date_value is None:
        return None

    # catches NaT, NaN, None
    if pd.isna(date_value):
        return None

    # already datetime
    if isinstance(date_value, datetime):
        return date_value

    # string parsing
    try:
        return datetime.strptime(date_value, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def diff_from_previous(prev, curr):
    changes = {}
    if prev is not None:
        for col in numeric_cols:
            d = curr[col] - prev[col]
            changes[col] = d

    days_since_previous = 0
    curr_date = safe_parse(curr.get("modified_date"))
    curr_date_available = safe_parse(curr.get("available_date"))
    if prev is not None:
        prev_date = safe_parse(prev.get("modified_date"))

        if prev_date is None or curr_date is None:
            days_since_previous = 0
        else:
            days_since_previous = (curr_date - prev_date).days

    available_modified_diff_days = 0
    if curr_date is not None and curr_date_available is not None:
        available_modified_diff_days = (curr_date_available - curr_date).days

    return {
        "nutrient_changes": changes,
        "days_since_previous_version": days_since_previous,
        "available_modified_diff_days": available_modified_diff_days,
    }


def build_versions(group: pd.DataFrame):
    rows = group.sort_values("modified_date").to_dict(orient="records")
    rows = [clean_row(r) for r in rows]

    version_docs = []
    previous = None

    for i, row in enumerate(rows):
        stats = diff_from_previous(previous, row)
        if i < len(rows):
            version_docs.append({
                "owner": owner_docs[row["brand_owner"]],
                "version": i + 1,
                "modified_date": row["modified_date"],
                **stats,
            })
        previous = row

    return rows[-1], version_docs


df = pd.read_csv("./fda_approved_food_items_w_nutrient_info.csv",
                 dtype={"gtin_upc": str})
df = df.dropna(subset=["brand_owner"])

client = MongoClient("mongodb://localhost:27017/")
mydb = client["testdb"]
products_col = mydb["products"]
owners_col = mydb["owners"]
product_version_col = mydb["product_version"]

products_col.drop()
owners_col.drop()
product_version_col.drop()

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
for i, row in owner_stats.iterrows():
    owner_docs[row["brand_owner"]] = {
        "_id": result.inserted_ids[i],
        "name": row["brand_owner"],
        "product_count": row["product_count"]
    }

product_rows = []
version_rows = []

for gtin, group in df.groupby("gtin_upc"):
    current_row, version_docs = build_versions(group)

    product_id = ObjectId()

    current_row["_id"] = product_id
    current_row["owner"] = owner_docs[current_row["brand_owner"]]
    del current_row["brand_owner"]
    current_row["nutri_grade"] = compute_nutri_score(current_row)
    product_rows.append(current_row)

    for v in version_docs:
        v["product_id"] = product_id
        v["gtin_upc"] = gtin
        version_rows.append(v)

BATCH_SIZE = 10_000
for i in tqdm(range(0, len(product_rows), BATCH_SIZE), desc="Inserting products"):
    products_col.insert_many(product_rows[i:i + BATCH_SIZE])

if version_rows:
    for i in tqdm(range(0, len(version_rows), BATCH_SIZE), desc="Inserting versions"):
        product_version_col.insert_many(version_rows[i:i + BATCH_SIZE])

print(client.list_database_names())
print(mydb.list_collection_names())
