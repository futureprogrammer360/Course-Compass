"""api.py

API providing access to the database that stores course data
"""

import os
import re
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, Path, Query
from fastapi.middleware.cors import CORSMiddleware
import motor.motor_asyncio

import utils

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

uri = os.getenv("MONGODB_URI")
client = motor.motor_asyncio.AsyncIOMotorClient(uri)
db = client["db"]

synonymous_department_codes = utils.load_synonyms("synonymous_department_codes")


@app.get("/courses/{university_id}")
async def get_courses(
    university_id: Annotated[str, Path(title="University ID")],
    limit: Annotated[int, Query(gt=0)] = None,
    query: str = None
):
    """Get courses associated with a particular university

    If a query is given, get list of courses with matching course numbers (up to limit, if given)
    If no query is given, get list of all courses associated with given university (up to limit, if given)

    Args:
        university_id: University ID
        limit: Maximum number of courses returned
        query: Query to be matched against course numbers

    Returns:
        A list of dicts containing data on courses
    """
    pipelines = []
    if query:
        query = query.upper()
        queries = [query]

        # If query starts with a department code with synonyms, create query variations from synonyms
        match = re.match("[A-Z]+", query)
        if match is not None and match.group() in synonymous_department_codes:
            for synonymous_department_code in synonymous_department_codes[match.group()]:
                queries.append(re.sub("[A-Z]+", synonymous_department_code, query, count=1))

        # Create an aggregation pipeline for each variation of the query
        for query in queries:
            pipeline = [
                {
                    "$search": {
                        "index": "courses-index",
                        "compound": {
                            "should": [
                                {  # Exact full text matching, accepts mapped department code synonyms
                                    "text": {
                                        "query": query,
                                        "path": "number",
                                        "synonyms": "department_codes_mapping"
                                    }
                                },
                                {  # Fuzzy full text matching
                                    "text": {
                                        "query": query,
                                        "path": "number",
                                        "fuzzy": {
                                            "maxEdits": 1,
                                            "prefixLength": 1
                                        }
                                    }
                                },
                                {  # Exact autocomplete matching
                                    "autocomplete": {
                                        "query": query,
                                        "path": "number",
                                        "tokenOrder": "sequential"
                                    }
                                },
                                {  # Fuzzy autocomplete matching
                                    "autocomplete": {
                                        "query": query,
                                        "path": "number",
                                        "fuzzy": {
                                            "maxEdits": 1,
                                            "prefixLength": 1
                                        },
                                        "tokenOrder": "sequential"
                                    }
                                }
                            ],
                            "filter": [
                                {
                                    "equals": {
                                        "path": "university_id",
                                        "value": university_id
                                    }
                                }
                            ],
                            "minimumShouldMatch": 2
                        }
                    }
                }
            ]
            pipelines.append(pipeline)
    else:
        pipeline = [
            {
                "$search": {
                    "index": "courses-index",
                    "equals": {
                        "path": "university_id",
                        "value": university_id
                    }
                }
            }
        ]
        pipelines.append(pipeline)

    if limit:
        for pipeline in pipelines:
            pipeline.append({"$limit": limit})

    for pipeline in pipelines:
        documents = db["courses"].aggregate(pipeline)
        documents = await documents.to_list()
        if len(documents) > 0:
            break

    return documents
