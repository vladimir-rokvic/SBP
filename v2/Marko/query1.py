from pymongo import MongoClient
import json

client = MongoClient("mongodb://localhost:27017/")
db = client["optimizovano"]
collection = db["products"]

collection.create_index([
    ("branded_food_category", 1),
    ("Protein-G", 1),
    ("Total lipid (fat)-G", 1),
    ("Energy-KCAL", 1)
])

pipeline = [
    {
        "$match": {
            "branded_food_category": {"$exists": True, "$ne": None},
            "Protein-G": {"$gt": 0},
            "Total lipid (fat)-G": {"$gt": 0},
            "Energy-KCAL": {"$gt": 0}
        }
    },
    {
        "$project": {
            "_id": 0,
            "branded_food_category": 1,
            "protein": "$Protein-G",
            "fat": "$Total lipid (fat)-G",
            "energy": "$Energy-KCAL",
            "saturated": "$Fatty acids, total saturated-G",
            "carbs": "$Carbohydrate, by difference-G",
            "fiber": "$Fiber, total dietary-G",
            "sugar": "$Sugars, total including NLEA-G",
            "sodium": "$Sodium, Na-MG",
            "serving_size": 1,
            "unsaturated_fat": {
                "$add": [
                    {"$ifNull": ["$Fatty acids, total monounsaturated-G", 0]},
                    {"$ifNull": ["$Fatty acids, total polyunsaturated-G", 0]}
                ]
            },
            "net_carbs": {
                "$subtract": [
                    {"$ifNull": ["$Carbohydrate, by difference-G", 0]},
                    {"$ifNull": ["$Fiber, total dietary-G", 0]}
                ]
            },
            "sodium_per_serving": {
                "$cond": [
                    {"$gt": ["$serving_size", 0]},
                    {
                        "$multiply": [
                            {"$divide": [{"$ifNull": ["$Sodium, Na-MG", 0]}, 100]},
                            "$serving_size"
                        ]
                    },
                    0
                ]
            },
            "calories_from_protein": {"$multiply": ["$Protein-G", 4]},
            "calories_from_fat": {"$multiply": ["$Total lipid (fat)-G", 9]},
            "calories_from_carbs": {
                "$multiply": [{"$ifNull": ["$Carbohydrate, by difference-G", 0]}, 4]
            }
        }
    },
    {
        "$group": {
            "_id": "$branded_food_category",
            "avg_protein": {"$avg": "$protein"},
            "avg_fat": {"$avg": "$fat"},
            "avg_energy": {"$avg": "$energy"},
            "avg_saturated": {"$avg": "$saturated"},
            "avg_unsaturated_fat": {"$avg": "$unsaturated_fat"},
            "avg_carbs": {"$avg": "$carbs"},
            "avg_fiber": {"$avg": "$fiber"},
            "avg_sugar": {"$avg": "$sugar"},
            "avg_net_carbs": {"$avg": "$net_carbs"},
            "avg_sodium_per_serving": {"$avg": "$sodium_per_serving"},
            "avg_cal_protein": {"$avg": "$calories_from_protein"},
            "avg_cal_fat": {"$avg": "$calories_from_fat"},
            "avg_cal_carbs": {"$avg": "$calories_from_carbs"},
            "total_products": {"$sum": 1},
            "high_protein_count": {"$sum": {"$cond": [{"$gte": ["$protein", 20]}, 1, 0]}},
            "low_fat_count": {"$sum": {"$cond": [{"$lte": ["$fat", 5]}, 1, 0]}},
            "high_fiber_count": {"$sum": {"$cond": [{"$gte": ["$fiber", 5]}, 1, 0]}},
            "high_sodium_count": {
                "$sum": {"$cond": [{"$gt": ["$sodium_per_serving", 600]}, 1, 0]}
            },
            "low_sugar_count": {"$sum": {"$cond": [{"$lte": ["$sugar", 2]}, 1, 0]}}
        }
    },
    {
        "$project": {
            "_id": 0,
            "category": "$_id",
            "total_products": 1,
            "avg_protein": {"$round": ["$avg_protein", 2]},
            "avg_fat": {"$round": ["$avg_fat", 2]},
            "avg_energy": {"$round": ["$avg_energy", 2]},
            "avg_fiber": {"$round": ["$avg_fiber", 2]},
            "avg_sugar": {"$round": ["$avg_sugar", 2]},
            "avg_net_carbs": {"$round": ["$avg_net_carbs", 2]},
            "avg_sodium_per_serving": {"$round": ["$avg_sodium_per_serving", 2]},
            "protein_fat_ratio": {
                "$round": [{"$divide": ["$avg_protein", "$avg_fat"]}, 4]
            },
            "protein_per_100kcal": {
                "$round": [
                    {"$multiply": [{"$divide": ["$avg_protein", "$avg_energy"]}, 100]},
                    3
                ]
            },
            "fat_per_100kcal": {
                "$round": [
                    {"$multiply": [{"$divide": ["$avg_fat", "$avg_energy"]}, 100]},
                    3
                ]
            },
            "saturated_fat_share": {
                "$round": [
                    {
                        "$cond": [
                            {"$gt": ["$avg_fat", 0]},
                            {"$multiply": [{"$divide": ["$avg_saturated", "$avg_fat"]}, 100]},
                            0
                        ]
                    },
                    2
                ]
            },
            "unsaturated_fat_share": {
                "$round": [
                    {
                        "$cond": [
                            {"$gt": ["$avg_fat", 0]},
                            {
                                "$multiply": [
                                    {"$divide": ["$avg_unsaturated_fat", "$avg_fat"]},
                                    100
                                ]
                            },
                            0
                        ]
                    },
                    2
                ]
            },
            "sat_unsat_ratio": {
                "$round": [
                    {
                        "$cond": [
                            {"$gt": ["$avg_unsaturated_fat", 0]},
                            {"$divide": ["$avg_saturated", "$avg_unsaturated_fat"]},
                            None
                        ]
                    },
                    4
                ]
            },
            "macronutrient_balance": {
                "$round": [
                    {
                        "$divide": [
                            "$avg_protein",
                            {"$add": ["$avg_protein", "$avg_fat", "$avg_carbs"]}
                        ]
                    },
                    4
                ]
            },
            "calorie_distribution": {
                "protein_pct": {
                    "$round": [
                        {"$multiply": [{"$divide": ["$avg_cal_protein", "$avg_energy"]}, 100]},
                        1
                    ]
                },
                "fat_pct": {
                    "$round": [
                        {"$multiply": [{"$divide": ["$avg_cal_fat", "$avg_energy"]}, 100]},
                        1
                    ]
                },
                "carbs_pct": {
                    "$round": [
                        {"$multiply": [{"$divide": ["$avg_cal_carbs", "$avg_energy"]}, 100]},
                        1
                    ]
                }
            },
            "high_protein_pct": {
                "$round": [
                    {"$multiply": [{"$divide": ["$high_protein_count", "$total_products"]}, 100]},
                    1
                ]
            },
            "low_fat_pct": {
                "$round": [
                    {"$multiply": [{"$divide": ["$low_fat_count", "$total_products"]}, 100]},
                    1
                ]
            },
            "high_fiber_pct": {
                "$round": [
                    {"$multiply": [{"$divide": ["$high_fiber_count", "$total_products"]}, 100]},
                    1
                ]
            },
            "high_sodium_pct": {
                "$round": [
                    {"$multiply": [{"$divide": ["$high_sodium_count", "$total_products"]}, 100]},
                    1
                ]
            },
            "low_sugar_pct": {
                "$round": [
                    {"$multiply": [{"$divide": ["$low_sugar_count", "$total_products"]}, 100]},
                    1
                ]
            },
            "sodium_risk": {
                "$switch": {
                    "branches": [
                        {"case": {"$gte": ["$avg_sodium_per_serving", 600]}, "then": "visok"},
                        {"case": {"$gte": ["$avg_sodium_per_serving", 300]}, "then": "umeren"}
                    ],
                    "default": "nizak"
                }
            },
            "nutritional_grade": {
                "$switch": {
                    "branches": [
                        {
                            "case": {
                                "$and": [
                                    {"$gte": [{"$divide": ["$avg_protein", "$avg_fat"]}, 2.0]},
                                    {"$lte": ["$avg_saturated", 3.0]},
                                    {"$gte": ["$avg_fiber", 3.0]},
                                    {"$lte": ["$avg_sugar", 5.0]}
                                ]
                            },
                            "then": "A"
                        },
                        {
                            "case": {
                                "$and": [
                                    {"$gte": [{"$divide": ["$avg_protein", "$avg_fat"]}, 1.0]},
                                    {"$lte": ["$avg_saturated", 5.0]},
                                    {"$gte": ["$avg_fiber", 1.5]}
                                ]
                            },
                            "then": "B"
                        },
                        {
                            "case": {
                                "$and": [
                                    {"$gte": [{"$divide": ["$avg_protein", "$avg_fat"]}, 0.5]},
                                    {"$lte": ["$avg_saturated", 8.0]}
                                ]
                            },
                            "then": "C"
                        },
                        {
                            "case": {"$gte": [{"$divide": ["$avg_protein", "$avg_fat"]}, 0.2]},
                            "then": "D"
                        }
                    ],
                    "default": "F"
                }
            }
        }
    },
    {"$sort": {"protein_fat_ratio": -1}},
    {"$limit": 15}
]

results = list(collection.aggregate(pipeline))

print(json.dumps(results, indent=2, ensure_ascii=False))

client.close()
