"""utils.py

API utilities
"""

import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

uri = os.getenv("MONGODB_URI")
client = MongoClient(uri)
db = client["db"]


def load_synonyms(collection: str) -> dict:
    """Load synonyms stored in specified collection of the database

    Given name of a collection in the database, load all documents in collection (each document
    listing a group of synonyms) and return the adjacency list representation of a graph
    that connects all the synonyms

    If collection coll has 2 documents with synonym fields [a, b, c] and [x, y], load_synonyms(coll) returns
    {
        a: [b, c],
        b: [a, c],
        c: [a, b],
        x: [y],
        y: [x]
    }

    Args:
        collection: name of the collection storing documents, whose synonyms field lists synonyms

    Returns:
        A dict that maps strings to a list of their synonyms as defined in the specified collection
    """
    synonyms_map = {}
    documents = db[collection].find().to_list()
    for document in documents:
        synonyms = document["synonyms"]
        for i, synonym in enumerate(synonyms):
            synonyms_map[synonym] = synonyms[:i] + synonyms[i + 1:]
    return synonyms_map
