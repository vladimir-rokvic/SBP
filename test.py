import pandas as pd
from datetime import datetime

df = pd.read_csv('./fda_approved_food_items_w_nutrient_info.csv')

date_cols = ['modified_date', 'available_date']
a = df.isnull().sum()
print(a)

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


for i, row in df.iterrows():
    prev_date = safe_parse(row["modified_date"])
    print(type(prev_date))
    prev_date = safe_parse(row["available_date"])
    print(type(prev_date))
