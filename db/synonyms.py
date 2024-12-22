"""synonyms.py

Program that writes synonym mappings to database
"""

import os
import json

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

uri = os.getenv("MONGODB_URI")
client = MongoClient(uri)
db = client["db"]

for file in os.listdir("synonyms"):
    collection_name = f"synonymous_{os.path.splitext(file)[0]}"
    with open(os.path.join("synonyms", file), "r") as file:
        synonyms = json.load(file)

    for key in synonyms:
        _id = key.replace(" ", "_").lower()
        if db[collection_name].find_one({"_id": _id}):
            print(f"Synonym mapping {_id} already in database, skipping")
        else:
            mapping_data = {
                "mappingType": "equivalent",
                "synonyms": synonyms[key],
                "_id": _id
            }
            db[collection_name].insert_one(mapping_data)
            print(f"Added synonym mapping {_id}")
