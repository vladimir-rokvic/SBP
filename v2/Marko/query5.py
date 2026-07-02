from pymongo import MongoClient
import json

client = MongoClient("mongodb://localhost:27017/")
db = client["projectdb"]
collection = db["products"]

collection.create_index([
    ("branded_food_category", 1),
    ("Energy-KCAL", 1),
    ("serving_size", 1)
])

pipeline = [
    {
        "$match": {
            "branded_food_category": {"$exists": True, "$ne": None},
            "Energy-KCAL": {"$gt": 0},
            "Iron, Fe-MG": {"$exists": True, "$ne": None},
            "Calcium, Ca-MG": {"$exists": True, "$ne": None},
            "Potassium, K-MG": {"$exists": True, "$ne": None},
            "Vitamin C, total ascorbic acid-MG": {"$exists": True, "$ne": None},
            "Fiber, total dietary-G": {"$exists": True, "$ne": None},
            "serving_size": {"$gt": 0}
        }
    },
    {"$sort": {"branded_food_category": 1}},
    {
        "$project": {
            "_id": 0,
            "branded_food_category": 1,
            "description": 1,
            "energy": "$Energy-KCAL",
            "iron": "$Iron, Fe-MG",
            "calcium": "$Calcium, Ca-MG",
            "potassium": "$Potassium, K-MG",
            "vitaminC": "$Vitamin C, total ascorbic acid-MG",
            "fiber": "$Fiber, total dietary-G",
            "protein": {"$ifNull": ["$Protein-G", 0]},
            "sodium": {"$ifNull": ["$Sodium, Na-MG", 0]},
            "sugar": {"$ifNull": ["$Sugars, total including NLEA-G", 0]},
            "vitaminA": {"$ifNull": ["$Vitamin A, IU-IU", 0]},
            "vitaminD": {"$ifNull": ["$Vitamin D (D2 + D3)-UG", 0]},
            "magnesium": {"$ifNull": ["$Magnesium, Mg-MG", 0]},
            "zinc": {"$ifNull": ["$Zinc, Zn-MG", 0]},
            "serving_size": 1,
            "protein_per_100kcal": {
                "$multiply": [
                    {"$divide": [{"$ifNull": ["$Protein-G", 0]}, "$Energy-KCAL"]},
                    100
                ]
            },
            "fat_per_100kcal": {
                "$multiply": [
                    {"$divide": [{"$ifNull": ["$Total lipid (fat)-G", 0]}, "$Energy-KCAL"]},
                    100
                ]
            },
            "fiber_per_100kcal": {
                "$multiply": [
                    {"$divide": ["$Fiber, total dietary-G", "$Energy-KCAL"]},
                    100
                ]
            },
            "sodium_per_serving": {
                "$multiply": [
                    {"$divide": [{"$ifNull": ["$Sodium, Na-MG", 0]}, 100]},
                    "$serving_size"
                ]
            },
            "iron_per_serving": {
                "$multiply": [
                    {"$divide": ["$Iron, Fe-MG", 100]},
                    "$serving_size"
                ]
            },
            "calcium_per_serving": {
                "$multiply": [
                    {"$divide": ["$Calcium, Ca-MG", 100]},
                    "$serving_size"
                ]
            },
            "is_micronutrient_rich": {
                "$and": [
                    {"$gte": ["$Iron, Fe-MG", 2]},
                    {"$gte": ["$Calcium, Ca-MG", 100]},
                    {"$gte": ["$Potassium, K-MG", 200]}
                ]
            },
            "is_penalized": {
                "$or": [
                    {
                        "$gt": [
                            {
                                "$multiply": [
                                    {"$divide": [{"$ifNull": ["$Sodium, Na-MG", 0]}, 100]},
                                    "$serving_size"
                                ]
                            },
                            600
                        ]
                    },
                    {"$gt": [{"$ifNull": ["$Sugars, total including NLEA-G", 0]}, 15]},
                    {"$gt": [{"$ifNull": ["$Fatty acids, total saturated-G", 0]}, 8]}
                ]
            },
            "base_score": {
                "$add": [
                    {"$divide": [{"$divide": ["$Iron, Fe-MG", "$Energy-KCAL"]}, 18.0]},
                    {"$divide": [{"$divide": ["$Calcium, Ca-MG", "$Energy-KCAL"]}, 30.0]},
                    {"$divide": [{"$divide": ["$Potassium, K-MG", "$Energy-KCAL"]}, 70.0]},
                    {
                        "$divide": [
                            {"$divide": ["$Vitamin C, total ascorbic acid-MG", "$Energy-KCAL"]},
                            10.0
                        ]
                    },
                    {"$divide": [{"$divide": ["$Fiber, total dietary-G", "$Energy-KCAL"]}, 2.5]},
                    {
                        "$divide": [
                            {"$divide": [{"$ifNull": ["$Magnesium, Mg-MG", 0]}, "$Energy-KCAL"]},
                            4.2
                        ]
                    },
                    {
                        "$divide": [
                            {"$divide": [{"$ifNull": ["$Zinc, Zn-MG", 0]}, "$Energy-KCAL"]},
                            0.11
                        ]
                    },
                    {
                        "$divide": [
                            {"$divide": [{"$ifNull": ["$Vitamin A, IU-IU", 0]}, "$Energy-KCAL"]},
                            90.0
                        ]
                    },
                    {
                        "$divide": [
                            {"$divide": [{"$ifNull": ["$Vitamin D (D2 + D3)-UG", 0]}, "$Energy-KCAL"]},
                            0.2
                        ]
                    }
                ]
            },
            "total_penalty": {
                "$add": [
                    {
                        "$cond": [
                            {"$gt": [{"$ifNull": ["$Sodium, Na-MG", 0]}, 0]},
                            {"$divide": [{"$divide": ["$Sodium, Na-MG", "$Energy-KCAL"]}, 23.0]},
                            0
                        ]
                    },
                    {
                        "$cond": [
                            {"$gt": [{"$ifNull": ["$Sugars, total including NLEA-G", 0]}, 0]},
                            {
                                "$divide": [
                                    {"$divide": ["$Sugars, total including NLEA-G", "$Energy-KCAL"]},
                                    5.0
                                ]
                            },
                            0
                        ]
                    },
                    {
                        "$cond": [
                            {"$gt": [{"$ifNull": ["$Fatty acids, total saturated-G", 0]}, 0]},
                            {
                                "$divide": [
                                    {"$divide": ["$Fatty acids, total saturated-G", "$Energy-KCAL"]},
                                    2.2
                                ]
                            },
                            0
                        ]
                    }
                ]
            }
        }
    },
    {
        "$project": {
            "branded_food_category": 1,
            "description": 1,
            "energy": 1,
            "iron": 1,
            "calcium": 1,
            "potassium": 1,
            "vitaminC": 1,
            "fiber": 1,
            "protein": 1,
            "sodium": 1,
            "sugar": 1,
            "vitaminA": 1,
            "vitaminD": 1,
            "magnesium": 1,
            "zinc": 1,
            "serving_size": 1,
            "protein_per_100kcal": 1,
            "fat_per_100kcal": 1,
            "fiber_per_100kcal": 1,
            "sodium_per_serving": 1,
            "iron_per_serving": 1,
            "calcium_per_serving": 1,
            "is_micronutrient_rich": 1,
            "is_penalized": 1,
            "base_score": 1,
            "total_penalty": 1,
            "net_score": {"$subtract": ["$base_score", "$total_penalty"]}
        }
    },
    {
        "$group": {
            "_id": "$branded_food_category",
            "avg_energy": {"$avg": "$energy"},
            "avg_protein": {"$avg": "$protein"},
            "avg_fiber": {"$avg": "$fiber"},
            "avg_sodium": {"$avg": "$sodium"},
            "avg_sugar": {"$avg": "$sugar"},
            "avg_iron": {"$avg": "$iron"},
            "avg_calcium": {"$avg": "$calcium"},
            "avg_potassium": {"$avg": "$potassium"},
            "avg_vitaminC": {"$avg": "$vitaminC"},
            "avg_vitaminA": {"$avg": "$vitaminA"},
            "avg_vitaminD": {"$avg": "$vitaminD"},
            "avg_magnesium": {"$avg": "$magnesium"},
            "avg_zinc": {"$avg": "$zinc"},
            "avg_protein_per_100kcal": {"$avg": "$protein_per_100kcal"},
            "avg_fat_per_100kcal": {"$avg": "$fat_per_100kcal"},
            "avg_fiber_per_100kcal": {"$avg": "$fiber_per_100kcal"},
            "avg_sodium_per_serving": {"$avg": "$sodium_per_serving"},
            "avg_iron_per_serving": {"$avg": "$iron_per_serving"},
            "avg_calcium_per_serving": {"$avg": "$calcium_per_serving"},
            "avg_base_score": {"$avg": "$base_score"},
            "avg_total_penalty": {"$avg": "$total_penalty"},
            "avg_net_score": {"$avg": "$net_score"},
            "max_net_score": {"$max": "$net_score"},
            "min_net_score": {"$min": "$net_score"},
            "total_products": {"$sum": 1},
            "micronutrient_rich_count": {"$sum": {"$cond": ["$is_micronutrient_rich", 1, 0]}},
            "penalized_count": {"$sum": {"$cond": ["$is_penalized", 1, 0]}},
            "best_product": {
                "$top": {
                    "output": {
                        "description": "$description",
                        "net_score": "$net_score"
                    },
                    "sortBy": {"net_score": -1}
                }
            },
            "worst_product": {
                "$top": {
                    "output": {
                        "description": "$description",
                        "net_score": "$net_score"
                    },
                    "sortBy": {"net_score": 1}
                }
            },
            "highest_iron_per_serving_product": {
                "$top": {
                    "output": {
                        "description": "$description",
                        "iron_per_serving": "$iron_per_serving"
                    },
                    "sortBy": {"iron_per_serving": -1}
                }
            },
            "highest_calcium_per_serving_product": {
                "$top": {
                    "output": {
                        "description": "$description",
                        "calcium_per_serving": "$calcium_per_serving"
                    },
                    "sortBy": {"calcium_per_serving": -1}
                }
            },
            "most_penalized_product": {
                "$top": {
                    "output": {
                        "description": "$description",
                        "total_penalty": "$total_penalty"
                    },
                    "sortBy": {"total_penalty": -1}
                }
            }
        }
    },
    {
        "$project": {
            "_id": 0,
            "category": "$_id",
            "total_products": 1,
            "avg_energy": {"$round": ["$avg_energy", 2]},
            "avg_protein": {"$round": ["$avg_protein", 2]},
            "avg_fiber": {"$round": ["$avg_fiber", 3]},
            "avg_sodium": {"$round": ["$avg_sodium", 2]},
            "avg_sugar": {"$round": ["$avg_sugar", 2]},
            "avg_iron": {"$round": ["$avg_iron", 3]},
            "avg_calcium": {"$round": ["$avg_calcium", 2]},
            "avg_potassium": {"$round": ["$avg_potassium", 2]},
            "avg_vitaminC": {"$round": ["$avg_vitaminC", 2]},
            "avg_vitaminA": {"$round": ["$avg_vitaminA", 2]},
            "avg_vitaminD": {"$round": ["$avg_vitaminD", 3]},
            "avg_magnesium": {"$round": ["$avg_magnesium", 2]},
            "avg_zinc": {"$round": ["$avg_zinc", 3]},
            "avg_protein_per_100kcal": {"$round": ["$avg_protein_per_100kcal", 3]},
            "avg_fat_per_100kcal": {"$round": ["$avg_fat_per_100kcal", 3]},
            "avg_fiber_per_100kcal": {"$round": ["$avg_fiber_per_100kcal", 3]},
            "avg_sodium_per_serving": {"$round": ["$avg_sodium_per_serving", 2]},
            "avg_iron_per_serving": {"$round": ["$avg_iron_per_serving", 3]},
            "avg_calcium_per_serving": {"$round": ["$avg_calcium_per_serving", 2]},
            "avg_base_score": {"$round": ["$avg_base_score", 4]},
            "avg_total_penalty": {"$round": ["$avg_total_penalty", 4]},
            "avg_net_score": {"$round": ["$avg_net_score", 4]},
            "max_net_score": {"$round": ["$max_net_score", 4]},
            "min_net_score": {"$round": ["$min_net_score", 4]},
            "score_range": {
                "$round": [
                    {"$subtract": ["$max_net_score", "$min_net_score"]},
                    4
                ]
            },
            "micronutrient_rich_pct": {
                "$round": [
                    {"$multiply": [{"$divide": ["$micronutrient_rich_count", "$total_products"]}, 100]},
                    1
                ]
            },
            "penalized_pct": {
                "$round": [
                    {"$multiply": [{"$divide": ["$penalized_count", "$total_products"]}, 100]},
                    1
                ]
            },
            "nutritional_efficiency": {
                "$round": [
                    {
                        "$cond": [
                            {"$gt": ["$avg_total_penalty", 0]},
                            {"$divide": ["$avg_base_score", "$avg_total_penalty"]},
                            "$avg_base_score"
                        ]
                    },
                    4
                ]
            },
            "nutrient_density_grade": {
                "$switch": {
                    "branches": [
                        {
                            "case": {
                                "$and": [
                                    {"$gte": ["$avg_net_score", 0.5]},
                                    {"$lte": ["$avg_total_penalty", 0.3]},
                                    {"$gte": ["$avg_fiber_per_100kcal", 2.0]}
                                ]
                            },
                            "then": "A"
                        },
                        {
                            "case": {
                                "$and": [
                                    {"$gte": ["$avg_net_score", 0.3]},
                                    {"$lte": ["$avg_total_penalty", 0.6]}
                                ]
                            },
                            "then": "B"
                        },
                        {
                            "case": {
                                "$and": [
                                    {"$gte": ["$avg_net_score", 0.1]},
                                    {"$lte": ["$avg_total_penalty", 1.0]}
                                ]
                            },
                            "then": "C"
                        },
                        {
                            "case": {"$gte": ["$avg_net_score", 0]},
                            "then": "D"
                        }
                    ],
                    "default": "F"
                }
            },
            "overall_health_rating": {
                "$switch": {
                    "branches": [
                        {
                            "case": {
                                "$and": [
                                    {"$gte": ["$avg_net_score", 0.4]},
                                    {"$gte": ["$avg_protein_per_100kcal", 5]},
                                    {"$lte": ["$avg_sodium_per_serving", 300]},
                                    {
                                        "$gte": [
                                            "$micronutrient_rich_count",
                                            {"$multiply": ["$total_products", 0.3]}
                                        ]
                                    }
                                ]
                            },
                            "then": "odlican"
                        },
                        {
                            "case": {
                                "$and": [
                                    {"$gte": ["$avg_net_score", 0.2]},
                                    {"$lte": ["$avg_sodium_per_serving", 600]}
                                ]
                            },
                            "then": "dobar"
                        },
                        {
                            "case": {
                                "$or": [
                                    {"$gte": ["$avg_net_score", 0.0]},
                                    {"$lte": ["$avg_sodium_per_serving", 1000]}
                                ]
                            },
                            "then": "prosecan"
                        },
                        {
                            "case": {"$lt": ["$avg_net_score", 0]},
                            "then": "los"
                        }
                    ],
                    "default": "nedovoljno podataka"
                }
            },
            "best_product": 1,
            "worst_product": 1,
            "highest_iron_per_serving_product": 1,
            "highest_calcium_per_serving_product": 1,
            "most_penalized_product": 1
        }
    },
    {"$sort": {"avg_net_score": -1}},
    {"$limit": 20}
]

results = list(collection.aggregate(pipeline))

print(json.dumps(results, indent=2, ensure_ascii=False))

client.close()
