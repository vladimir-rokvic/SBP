from pymongo import MongoClient
import json

client = MongoClient("mongodb://localhost:27017/")

projectdb = client["projectdb"]

products = projectdb["products"]

pipeline = [
    {"$match": {"ingredients": {"$type": "string"}}},
    {
        "$group": {
            "_id": "$owner",
            "total": {"$sum": 1},
            "has_allergen": {
                "$sum": {
                    "$cond": [{
                        "$or": [
                            {"$regexMatch": {"input": "$ingredients", "regex": "nut", "options": "i"}},
                            {"$regexMatch": {"input": "$ingredients", "regex": "milk", "options": "i"}},
                            {"$regexMatch": {"input": "$ingredients", "regex": "egg", "options": "i"}},
                            {"$regexMatch": {"input": "$ingredients", "regex": "fish", "options": "i"}},
                            {"$regexMatch": {"input": "$ingredients", "regex": "wheat", "options": "i"}},
                        ]},
                             1,
                             0
                             ]
                }}
        }},
    {"$lookup": {
        "from": "owners",
        "localField": "_id",
        "foreignField": "_id",
        "as": "owner_info"
    }},
    {"$unwind": "$owner_info"},
    {"$project": {
        "owner_name": "$owner_info.name",
        "total": 1,
        "has_allergen": 1,
        "percent": {
            "$divide": ["$has_allergen", "$total"]
        }
    }},
    {"$sort": {"percent": -1}},
    {"$limit": 10}
]

#products.aggregate([
#    {
#        "$group": {
#            "_id": "$owner",
#            "total": {"$sum": 1},
#            "has_allergen": {
#                "$sum":{
#                    "$cond":[{
#                        "$or":[
#                            {"$regexMatch": {"input": "ingredients", "regex": "nut", "options": "i"}},
#                            {"$regexMatch": {"input": "ingredients", "regex": "milk", "options": "i"}},
#                            {"$regexMatch": {"input": "ingredients", "regex": "eggs", "options": "i"}},
#                        ]},
#                             1,
#                             0
#                             ]
#                }}
#        }},
#    {"$project": {
#        "owner_id": "$_id",
#        "total": 1,
#        "has_allergen": 1,
#        "percent": {
#            "$divide": ["has_allergen", "total"]
#        }
#    }},
#    {"$sort": {"percent": 1}},
#    {"$liimt": 10}
#])

import time

start = time.time()
results = list(products.aggregate(pipeline))
end = time.time()

# Get total docs examined via a separate count
total_docs = products.count_documents({})

print(f"Execution time: {end - start:.2f}s")
print(f"Total documents in collection: {total_docs}")
print(f"Results returned: {len(results)}")
for r in results:
    print(f"{r['owner_name']} — {r['percent']:.1f}% ({r['has_allergen']}/{r['total']})")
