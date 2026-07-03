from pymongo import MongoClient
import json

client = MongoClient("mongodb://localhost:27017/")
db = client["projectdb"]
collection = db["products"]

pipeline = [
    {
        "$match": {
            "branded_food_category": {"$exists": True, "$ne": None},
            "Sodium, Na-MG": {"$exists": True, "$ne": None},
            "Energy-KCAL": {"$exists": True, "$ne": None},
            "serving_size": {"$exists": True, "$ne": None}
        }
    },
    {
        "$project": {
            "_id": 0,
            "branded_food_category": 1,
            "description": 1,
            "sodium": {"$toDouble": "$Sodium, Na-MG"},
            "energy": {"$toDouble": "$Energy-KCAL"},
            "serving_size": {"$toDouble": "$serving_size"},
            "protein": {"$toDouble": "$Protein-G"},
            "fat": {"$toDouble": "$Total lipid (fat)-G"},
            "carbs": {"$toDouble": "$Carbohydrate, by difference-G"},
            "potassium": {"$toDouble": "$Potassium, K-MG"},
            "fiber": {"$toDouble": "$Fiber, total dietary-G"},
            "saturated": {"$toDouble": "$Fatty acids, total saturated-G"}
        }
    },
    {
        "$match": {
            "energy": {"$gt": 0},
            "serving_size": {"$gt": 0},
            "sodium": {"$gte": 0}
        }
    },
    {
        "$project": {
            "branded_food_category": 1,
            "description": 1,
            "sodium": 1,
            "energy": 1,
            "serving_size": 1,
            "protein": 1,
            "fat": 1,
            "carbs": 1,
            "potassium": 1,
            "fiber": 1,
            "saturated": 1,
            "sodium_per_100kcal": {"$multiply": [{"$divide": ["$sodium", "$energy"]}, 100]},
            "sodium_per_serving": {"$multiply": [{"$divide": ["$sodium", 100]}, "$serving_size"]},
            "energy_per_serving": {"$multiply": [{"$divide": ["$energy", 100]}, "$serving_size"]},
            "sodium_to_potassium_ratio": {
                "$cond": [
                    {"$gt": ["$potassium", 0]},
                    {"$divide": ["$sodium", "$potassium"]},
                    None
                ]
            },
            "sodium_to_protein_ratio": {
                "$cond": [
                    {"$gt": ["$protein", 0]},
                    {"$divide": ["$sodium", "$protein"]},
                    None
                ]
            },
            "sodium_density_score": {
                "$cond": [
                    {"$gt": ["$energy", 0]},
                    {
                        "$multiply": [
                            {"$divide": ["$sodium", "$energy"]},
                            {"$divide": ["$serving_size", 100]}
                        ]
                    },
                    None
                ]
            },
            "is_high_sodium": {
                "$cond": [
                    {"$gt": [{"$multiply": [{"$divide": ["$sodium", 100]}, "$serving_size"]}, 600]},
                    True,
                    False
                ]
            },
            "is_very_high_sodium": {
                "$cond": [
                    {"$gt": [{"$multiply": [{"$divide": ["$sodium", 100]}, "$serving_size"]}, 1500]},
                    True,
                    False
                ]
            },
            "exceeds_daily_value": {
                "$cond": [
                    {"$gt": [{"$multiply": [{"$divide": ["$sodium", 100]}, "$serving_size"]}, 2300]},
                    True,
                    False
                ]
            },
            "has_favorable_k_na": {
                "$cond": [
                    {
                        "$and": [
                            {"$gt": ["$potassium", 0]},
                            {"$lt": [{"$divide": ["$sodium", "$potassium"]}, 1.0]}
                        ]
                    },
                    True,
                    False
                ]
            }
        }
    },
    {
        "$group": {
            "_id": "$branded_food_category",
            "avg_sodium": {"$avg": "$sodium"},
            "avg_energy": {"$avg": "$energy"},
            "avg_serving_size": {"$avg": "$serving_size"},
            "avg_potassium": {"$avg": "$potassium"},
            "avg_protein": {"$avg": "$protein"},
            "avg_fiber": {"$avg": "$fiber"},
            "avg_saturated": {"$avg": "$saturated"},
            "avg_sodium_per_100kcal": {"$avg": "$sodium_per_100kcal"},
            "avg_sodium_per_serving": {"$avg": "$sodium_per_serving"},
            "avg_energy_per_serving": {"$avg": "$energy_per_serving"},
            "avg_sodium_to_potassium": {"$avg": "$sodium_to_potassium_ratio"},
            "avg_sodium_to_protein": {"$avg": "$sodium_to_protein_ratio"},
            "avg_sodium_density_score": {"$avg": "$sodium_density_score"},
            "max_sodium_per_serving": {"$max": "$sodium_per_serving"},
            "min_sodium_per_serving": {"$min": "$sodium_per_serving"},
            "total_products": {"$sum": 1},
            "high_sodium_count": {"$sum": {"$cond": ["$is_high_sodium", 1, 0]}},
            "very_high_sodium_count": {"$sum": {"$cond": ["$is_very_high_sodium", 1, 0]}},
            "exceeds_dv_count": {"$sum": {"$cond": ["$exceeds_daily_value", 1, 0]}},
            "favorable_k_na_count": {"$sum": {"$cond": ["$has_favorable_k_na", 1, 0]}},
            "products": {
                "$push": {
                    "description": "$description",
                    "sodium_per_serving": "$sodium_per_serving",
                    "sodium_per_100kcal": "$sodium_per_100kcal",
                    "sodium_to_potassium_ratio": "$sodium_to_potassium_ratio",
                    "energy_per_serving": "$energy_per_serving",
                    "sodium_density_score": "$sodium_density_score"
                }
            }
        }
    },
    {
        "$project": {
            "_id": 0,
            "category": "$_id",
            "total_products": 1,
            "avg_sodium": {"$round": ["$avg_sodium", 2]},
            "avg_energy": {"$round": ["$avg_energy", 2]},
            "avg_serving_size": {"$round": ["$avg_serving_size", 2]},
            "avg_potassium": {"$round": ["$avg_potassium", 2]},
            "avg_protein": {"$round": ["$avg_protein", 2]},
            "avg_fiber": {"$round": ["$avg_fiber", 3]},
            "avg_saturated": {"$round": ["$avg_saturated", 3]},
            "avg_sodium_per_100kcal": {"$round": ["$avg_sodium_per_100kcal", 2]},
            "avg_sodium_per_serving": {"$round": ["$avg_sodium_per_serving", 2]},
            "avg_energy_per_serving": {"$round": ["$avg_energy_per_serving", 2]},
            "avg_sodium_to_potassium": {"$round": ["$avg_sodium_to_potassium", 4]},
            "avg_sodium_to_protein": {"$round": ["$avg_sodium_to_protein", 4]},
            "avg_sodium_density_score": {"$round": ["$avg_sodium_density_score", 6]},
            "max_sodium_per_serving": {"$round": ["$max_sodium_per_serving", 2]},
            "min_sodium_per_serving": {"$round": ["$min_sodium_per_serving", 2]},
            "sodium_range": {
                "$round": [
                    {"$subtract": ["$max_sodium_per_serving", "$min_sodium_per_serving"]},
                    2
                ]
            },
            "high_sodium_pct": {
                "$round": [
                    {"$multiply": [{"$divide": ["$high_sodium_count", "$total_products"]}, 100]},
                    1
                ]
            },
            "very_high_sodium_pct": {
                "$round": [
                    {"$multiply": [{"$divide": ["$very_high_sodium_count", "$total_products"]}, 100]},
                    1
                ]
            },
            "exceeds_dv_pct": {
                "$round": [
                    {"$multiply": [{"$divide": ["$exceeds_dv_count", "$total_products"]}, 100]},
                    1
                ]
            },
            "favorable_k_na_pct": {
                "$round": [
                    {"$multiply": [{"$divide": ["$favorable_k_na_count", "$total_products"]}, 100]},
                    1
                ]
            },
            "sodium_risk_level": {
                "$switch": {
                    "branches": [
                        {
                            "case": {
                                "$and": [
                                    {"$gte": ["$avg_sodium_per_100kcal", 400]},
                                    {"$gte": ["$avg_sodium_to_potassium", 2.0]}
                                ]
                            },
                            "then": "kritican"
                        },
                        {
                            "case": {
                                "$or": [
                                    {"$gte": ["$avg_sodium_per_100kcal", 300]},
                                    {"$gte": ["$avg_sodium_to_potassium", 1.5]}
                                ]
                            },
                            "then": "visok"
                        },
                        {
                            "case": {
                                "$or": [
                                    {"$gte": ["$avg_sodium_per_100kcal", 150]},
                                    {"$gte": ["$avg_sodium_to_potassium", 1.0]}
                                ]
                            },
                            "then": "umeren"
                        }
                    ],
                    "default": "nizak"
                }
            },
            "cardiovascular_sodium_grade": {
                "$switch": {
                    "branches": [
                        {
                            "case": {
                                "$and": [
                                    {"$lte": ["$avg_sodium_per_serving", 140]},
                                    {"$lt": ["$avg_sodium_to_potassium", 0.5]}
                                ]
                            },
                            "then": "A"
                        },
                        {
                            "case": {
                                "$and": [
                                    {"$lte": ["$avg_sodium_per_serving", 300]},
                                    {"$lt": ["$avg_sodium_to_potassium", 1.0]}
                                ]
                            },
                            "then": "B"
                        },
                        {
                            "case": {
                                "$and": [
                                    {"$lte": ["$avg_sodium_per_serving", 600]},
                                    {"$lt": ["$avg_sodium_to_potassium", 1.5]}
                                ]
                            },
                            "then": "C"
                        },
                        {
                            "case": {"$lte": ["$avg_sodium_per_serving", 1500]},
                            "then": "D"
                        }
                    ],
                    "default": "F"
                }
            },
            "saltiest_product": {
                "$reduce": {
                    "input": "$products",
                    "initialValue": {"description": "", "sodium_per_serving": -1},
                    "in": {
                        "$cond": [
                            {
                                "$gt": [
                                    "$$this.sodium_per_serving",
                                    "$$value.sodium_per_serving"
                                ]
                            },
                            "$$this",
                            "$$value"
                        ]
                    }
                }
            },
            "least_salty_product": {
                "$reduce": {
                    "input": "$products",
                    "initialValue": {"description": "", "sodium_per_serving": 999999},
                    "in": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$gt": ["$$this.sodium_per_serving", 0]},
                                    {"$lt": ["$$this.sodium_per_serving", "$$value.sodium_per_serving"]}
                                ]
                            },
                            "$$this",
                            "$$value"
                        ]
                    }
                }
            },
            "best_k_na_product": {
                "$reduce": {
                    "input": "$products",
                    "initialValue": {"description": "", "sodium_to_potassium_ratio": 999},
                    "in": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$ne": ["$$this.sodium_to_potassium_ratio", None]},
                                    {"$gt": ["$$this.sodium_to_potassium_ratio", 0]},
                                    {
                                        "$lt": [
                                            "$$this.sodium_to_potassium_ratio",
                                            "$$value.sodium_to_potassium_ratio"
                                        ]
                                    }
                                ]
                            },
                            "$$this",
                            "$$value"
                        ]
                    }
                }
            },
            "highest_density_product": {
                "$reduce": {
                    "input": "$products",
                    "initialValue": {"description": "", "sodium_density_score": -1},
                    "in": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$ne": ["$$this.sodium_density_score", None]},
                                    {"$gt": ["$$this.sodium_density_score", "$$value.sodium_density_score"]}
                                ]
                            },
                            "$$this",
                            "$$value"
                        ]
                    }
                }
            }
        }
    },
    {"$sort": {"avg_sodium_per_100kcal": -1}}
]

results = list(collection.aggregate(pipeline))

print(json.dumps(results, indent=2, ensure_ascii=False))

client.close()
