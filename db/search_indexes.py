"""search_indexes.py

Program that creates Atlas Search Indexes
"""

import os
import json

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.operations import SearchIndexModel

load_dotenv()

uri = os.getenv("MONGODB_URI")
client = MongoClient(uri)
db = client["db"]

for file in os.listdir("search_indexes"):
    with open(os.path.join("search_indexes", file), "r") as file:
        index_data = json.load(file)
    name = index_data["name"]

    collection = db[index_data["collection"]]
    existing_indexes = collection.list_search_indexes().to_list()
    existing_index_names = [existing_index["name"] for existing_index in existing_indexes]
    if name in existing_index_names:
        print(f"Search index {name} already in collection {collection.name}, skipping")
    else:
        search_index_model = SearchIndexModel(
            name=name,
            definition=index_data["definition"]
        )
        collection.create_search_index(model=search_index_model)
        print(f"Created search index {name}")
