from pymongo import MongoClient
import json

client = MongoClient("mongodb://localhost:27017/")
db = client["optimizovano"]
collection = db["products"]

collection.create_index([
    ("branded_food_category", 1),
    ("Fiber, total dietary-G", 1),
    ("Carbohydrate, by difference-G", 1),
    ("Energy-KCAL", 1)
])

pipeline = [
    {
        "$match": {
            "branded_food_category": {"$exists": True, "$ne": None},
            "Fiber, total dietary-G": {"$exists": True, "$ne": None},
            "Carbohydrate, by difference-G": {"$exists": True, "$ne": None, "$gt": 0},
            "Energy-KCAL": {"$exists": True, "$ne": None, "$gt": 0}
        }
    },
    {"$sort": {"branded_food_category": 1}},
    {
        "$project": {
            "_id": 0,
            "branded_food_category": 1,
            "description": 1,
            "fiber": {"$ifNull": ["$Fiber, total dietary-G", 0]},
            "carbs": "$Carbohydrate, by difference-G",
            "energy": "$Energy-KCAL",
            "calcium": "$Calcium, Ca-MG",
            "iron": "$Iron, Fe-MG",
            "net_carbs": {
                "$subtract": [
                    "$Carbohydrate, by difference-G",
                    {"$ifNull": ["$Fiber, total dietary-G", 0]}
                ]
            },
            "fiber_share_in_carbs": {
                "$multiply": [
                    {
                        "$divide": [
                            {"$ifNull": ["$Fiber, total dietary-G", 0]},
                            "$Carbohydrate, by difference-G"
                        ]
                    },
                    100
                ]
            },
            "fiber_per_100kcal": {
                "$multiply": [
                    {"$divide": [{"$ifNull": ["$Fiber, total dietary-G", 0]}, "$Energy-KCAL"]},
                    100
                ]
            },
            "fiber_per_serving": {
                "$cond": [
                    {"$gt": [{"$ifNull": ["$serving_size", 0]}, 0]},
                    {
                        "$multiply": [
                            {"$divide": [{"$ifNull": ["$Fiber, total dietary-G", 0]}, 100]},
                            {"$ifNull": ["$serving_size", 0]}
                        ]
                    },
                    0
                ]
            },
            "sugar_to_fiber_ratio": {
                "$cond": [
                    {"$gt": [{"$ifNull": ["$Fiber, total dietary-G", 0]}, 0]},
                    {
                        "$divide": [
                            {"$ifNull": ["$Sugars, total including NLEA-G", 0]},
                            "$Fiber, total dietary-G"
                        ]
                    },
                    None
                ]
            },
            "sugar_to_fiber_sort_key": {
                "$cond": [
                    {"$gt": [{"$ifNull": ["$Fiber, total dietary-G", 0]}, 0]},
                    {
                        "$divide": [
                            {"$ifNull": ["$Sugars, total including NLEA-G", 0]},
                            "$Fiber, total dietary-G"
                        ]
                    },
                    999999999
                ]
            },
            "is_high_fiber": {"$gte": [{"$ifNull": ["$Fiber, total dietary-G", 0]}, 5]},
            "is_low_fiber": {"$lt": [{"$ifNull": ["$Fiber, total dietary-G", 0]}, 0.5]},
            "is_high_sugar": {"$gte": [{"$ifNull": ["$Sugars, total including NLEA-G", 0]}, 10]}
        }
    },
    {
        "$group": {
            "_id": "$branded_food_category",
            "avg_fiber": {"$avg": "$fiber"},
            "avg_carbs": {"$avg": "$carbs"},
            "avg_energy": {"$avg": "$energy"},
            "avg_net_carbs": {"$avg": "$net_carbs"},
            "avg_fiber_per_100kcal": {"$avg": "$fiber_per_100kcal"},
            "avg_fiber_share_in_carbs": {"$avg": "$fiber_share_in_carbs"},
            "avg_fiber_per_serving": {"$avg": "$fiber_per_serving"},
            "avg_sugar_to_fiber": {"$avg": "$sugar_to_fiber_ratio"},
            "avg_calcium": {"$avg": "$calcium"},
            "avg_iron": {"$avg": "$iron"},
            "total_products": {"$sum": 1},
            "high_fiber_count": {"$sum": {"$cond": ["$is_high_fiber", 1, 0]}},
            "low_fiber_count": {"$sum": {"$cond": ["$is_low_fiber", 1, 0]}},
            "high_sugar_count": {"$sum": {"$cond": ["$is_high_sugar", 1, 0]}},
            "max_fiber_product": {
                "$top": {
                    "sortBy": {"fiber": -1},
                    "output": {"description": "$description", "fiber": "$fiber"}
                }
            },
            "max_fiber_share_product": {
                "$top": {
                    "sortBy": {"fiber_share_in_carbs": -1},
                    "output": {
                        "description": "$description",
                        "fiber_share_in_carbs": "$fiber_share_in_carbs"
                    }
                }
            },
            "max_fiber_per_serving_product": {
                "$top": {
                    "sortBy": {"fiber_per_serving": -1},
                    "output": {
                        "description": "$description",
                        "fiber_per_serving": "$fiber_per_serving"
                    }
                }
            },
            "best_sugar_fiber_product": {
                "$top": {
                    "sortBy": {"sugar_to_fiber_sort_key": 1},
                    "output": {
                        "description": "$description",
                        "sugar_to_fiber_ratio": "$sugar_to_fiber_ratio"
                    }
                }
            }
        }
    },
    {
        "$project": {
            "_id": 0,
            "category": "$_id",
            "total_products": 1,
            "avg_fiber": {"$round": ["$avg_fiber", 3]},
            "avg_carbs": {"$round": ["$avg_carbs", 3]},
            "avg_energy": {"$round": ["$avg_energy", 2]},
            "avg_net_carbs": {"$round": ["$avg_net_carbs", 3]},
            "avg_fiber_per_100kcal": {"$round": ["$avg_fiber_per_100kcal", 3]},
            "avg_fiber_share_in_carbs": {"$round": ["$avg_fiber_share_in_carbs", 2]},
            "avg_fiber_per_serving": {"$round": ["$avg_fiber_per_serving", 3]},
            "avg_sugar_to_fiber": {"$round": ["$avg_sugar_to_fiber", 3]},
            "avg_calcium": {"$round": ["$avg_calcium", 2]},
            "avg_iron": {"$round": ["$avg_iron", 3]},
            "high_fiber_pct": {
                "$round": [
                    {"$multiply": [{"$divide": ["$high_fiber_count", "$total_products"]}, 100]},
                    1
                ]
            },
            "low_fiber_pct": {
                "$round": [
                    {"$multiply": [{"$divide": ["$low_fiber_count", "$total_products"]}, 100]},
                    1
                ]
            },
            "high_sugar_pct": {
                "$round": [
                    {"$multiply": [{"$divide": ["$high_sugar_count", "$total_products"]}, 100]},
                    1
                ]
            },
            "processing_flag": {
                "$switch": {
                    "branches": [
                        {"case": {"$lt": ["$avg_fiber", 0.5]}, "then": "visoko preradjeno"},
                        {
                            "case": {
                                "$and": [{"$gte": ["$avg_fiber", 0.5]}, {"$lt": ["$avg_fiber", 2.0]}]
                            },
                            "then": "umereno preradjeno"
                        },
                        {
                            "case": {
                                "$and": [{"$gte": ["$avg_fiber", 2.0]}, {"$lt": ["$avg_fiber", 5.0]}]
                            },
                            "then": "minimalno preradjeno"
                        }
                    ],
                    "default": "bogato vlaknima"
                }
            },
            "fiber_quality_score": {
                "$round": [
                    {
                        "$add": [
                            {"$multiply": ["$avg_fiber_per_100kcal", 2]},
                            {"$multiply": ["$avg_fiber_share_in_carbs", 0.1]},
                            {
                                "$cond": [
                                    {"$gt": ["$avg_sugar_to_fiber", 0]},
                                    {"$multiply": [{"$divide": [1, "$avg_sugar_to_fiber"]}, 5]},
                                    0
                                ]
                            }
                        ]
                    },
                    3
                ]
            },
            "max_fiber_product": 1,
            "max_fiber_share_product": 1,
            "max_fiber_per_serving_product": 1,
            "best_sugar_fiber_product": {
                "description": "$best_sugar_fiber_product.description",
                "sugar_to_fiber_ratio": {
                    "$cond": [
                        {"$eq": ["$best_sugar_fiber_product.sugar_to_fiber_ratio", None]},
                        None,
                        "$best_sugar_fiber_product.sugar_to_fiber_ratio"
                    ]
                }
            }
        }
    },
    {"$sort": {"avg_fiber": -1}}
]

results = list(collection.aggregate(pipeline))

print(json.dumps(results, indent=2, ensure_ascii=False))

client.close()
