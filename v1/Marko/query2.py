from pymongo import MongoClient
import json

client = MongoClient("mongodb://localhost:27017/")
db = client["projectdb"]
collection = db["products"]

pipeline = [
    {
        "$match": {
            "branded_food_category": {"$exists": True, "$ne": None},
            "Fiber, total dietary-G": {"$exists": True, "$ne": None},
            "Carbohydrate, by difference-G": {"$exists": True, "$ne": None},
            "Energy-KCAL": {"$exists": True, "$ne": None}
        }
    },
    {
        "$project": {
            "_id": 0,
            "branded_food_category": 1,
            "description": 1,
            "fiber": {"$toDouble": "$Fiber, total dietary-G"},
            "carbs": {"$toDouble": "$Carbohydrate, by difference-G"},
            "energy": {"$toDouble": "$Energy-KCAL"},
            "protein": {"$toDouble": "$Protein-G"},
            "fat": {"$toDouble": "$Total lipid (fat)-G"},
            "sugar": {"$toDouble": "$Sugars, total including NLEA-G"},
            "serving_size": {"$toDouble": "$serving_size"},
            "sodium": {"$toDouble": "$Sodium, Na-MG"},
            "calcium": {"$toDouble": "$Calcium, Ca-MG"},
            "iron": {"$toDouble": "$Iron, Fe-MG"}
        }
    },
    {
        "$match": {
            "energy": {"$gt": 0},
            "carbs": {"$gt": 0}
        }
    },
    {
        "$project": {
            "branded_food_category": 1,
            "description": 1,
            "fiber": 1,
            "carbs": 1,
            "energy": 1,
            "protein": 1,
            "fat": 1,
            "sugar": 1,
            "serving_size": 1,
            "sodium": 1,
            "calcium": 1,
            "iron": 1,
            "net_carbs": {"$subtract": ["$carbs", "$fiber"]},
            "fiber_share_in_carbs": {"$multiply": [{"$divide": ["$fiber", "$carbs"]}, 100]},
            "fiber_per_100kcal": {"$multiply": [{"$divide": ["$fiber", "$energy"]}, 100]},
            "fiber_per_serving": {
                "$cond": [
                    {"$gt": ["$serving_size", 0]},
                    {"$multiply": [{"$divide": ["$fiber", 100]}, "$serving_size"]},
                    0
                ]
            },
            "sugar_to_fiber_ratio": {
                "$cond": [
                    {"$gt": ["$fiber", 0]},
                    {"$divide": ["$sugar", "$fiber"]},
                    None
                ]
            },
            "is_high_fiber": {"$cond": [{"$gte": ["$fiber", 5]}, True, False]},
            "is_low_fiber": {"$cond": [{"$lt": ["$fiber", 0.5]}, True, False]},
            "is_high_sugar": {"$cond": [{"$gte": ["$sugar", 10]}, True, False]}
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
            "products": {
                "$push": {
                    "description": "$description",
                    "fiber": "$fiber",
                    "fiber_share_in_carbs": "$fiber_share_in_carbs",
                    "fiber_per_100kcal": "$fiber_per_100kcal",
                    "fiber_per_serving": "$fiber_per_serving",
                    "sugar_to_fiber_ratio": "$sugar_to_fiber_ratio",
                    "net_carbs": "$net_carbs"
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
                                "$and": [
                                    {"$gte": ["$avg_fiber", 0.5]},
                                    {"$lt": ["$avg_fiber", 2.0]}
                                ]
                            },
                            "then": "umereno preradjeno"
                        },
                        {
                            "case": {
                                "$and": [
                                    {"$gte": ["$avg_fiber", 2.0]},
                                    {"$lt": ["$avg_fiber", 5.0]}
                                ]
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
            "max_fiber_product": {
                "$reduce": {
                    "input": "$products",
                    "initialValue": {"description": "", "fiber": -1},
                    "in": {
                        "$cond": [
                            {"$gt": ["$$this.fiber", "$$value.fiber"]},
                            "$$this",
                            "$$value"
                        ]
                    }
                }
            },
            "max_fiber_share_product": {
                "$reduce": {
                    "input": "$products",
                    "initialValue": {"description": "", "fiber_share_in_carbs": -1},
                    "in": {
                        "$cond": [
                            {
                                "$gt": [
                                    "$$this.fiber_share_in_carbs",
                                    "$$value.fiber_share_in_carbs"
                                ]
                            },
                            "$$this",
                            "$$value"
                        ]
                    }
                }
            },
            "max_fiber_per_serving_product": {
                "$reduce": {
                    "input": "$products",
                    "initialValue": {"description": "", "fiber_per_serving": -1},
                    "in": {
                        "$cond": [
                            {
                                "$gt": [
                                    "$$this.fiber_per_serving",
                                    "$$value.fiber_per_serving"
                                ]
                            },
                            "$$this",
                            "$$value"
                        ]
                    }
                }
            },
            "best_sugar_fiber_product": {
                "$reduce": {
                    "input": "$products",
                    "initialValue": {"description": "", "sugar_to_fiber_ratio": 999},
                    "in": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$ne": ["$$this.sugar_to_fiber_ratio", None]},
                                    {
                                        "$lt": [
                                            "$$this.sugar_to_fiber_ratio",
                                            "$$value.sugar_to_fiber_ratio"
                                        ]
                                    }
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
    {"$sort": {"avg_fiber": -1}}
]

results = list(collection.aggregate(pipeline))

print(json.dumps(results, indent=2, ensure_ascii=False))

client.close()
