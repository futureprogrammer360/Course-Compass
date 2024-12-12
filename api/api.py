"""api.py

API providing access to the database that stores course data
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
import motor.motor_asyncio

load_dotenv()

app = FastAPI()

uri = os.getenv("MONGODB_URI")
client = motor.motor_asyncio.AsyncIOMotorClient(uri)
db = client["db"]


@app.get("/courses/{university_id}")
async def get_courses(university_id: str):
    """Get courses associated with a particular university"""
    documents = await db["courses"].find({
        "university_id": university_id
    }).to_list()

    if len(documents) == 0:
        return {"code": 404}
    return {"code": 200, "courses": documents}


@app.get("/course/{university_id}/{course_id}")
async def get_course(university_id: str, course_id: str):
    """Get a course by university ID and course ID"""
    document = await db["courses"].find_one({
        "_id": f"{university_id}-{course_id}"
    })

    if document is None:
        return {"code": 404}
    return {"code": 200, "course": document}
