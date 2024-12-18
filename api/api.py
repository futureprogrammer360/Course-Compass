"""api.py

API providing access to the database that stores course data
"""

import os
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
import motor.motor_asyncio

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

    Raises:
        HTTPException: No courses found with the given arguments
    """
    if query:
        pipeline = [
            {"$search": {"index": "courses-autocomplete", "autocomplete": {"query": query, "path": "number"}}},
            {"$match": {"university_id": university_id}}
        ]
        if limit:
            pipeline.append({"$limit": limit})
        documents = db["courses"].aggregate(pipeline)
    else:
        documents = db["courses"].find({
            "university_id": university_id
        })
        if limit:
            documents = documents.limit(limit)

    documents = await documents.to_list()
    if len(documents) == 0:
        raise HTTPException(status_code=404, detail="No courses found")
    return documents
