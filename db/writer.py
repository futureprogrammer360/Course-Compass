"""writer.py

Program that writes data on universities and courses to database
"""

import os
import json
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

with open(os.path.join("..", "universities.json"), "r") as file:
    universities = json.load(file)

uri = os.getenv("MONGODB_URI")
client = MongoClient(uri)
db = client["db"]

for university_id in os.listdir(os.path.join("..", "cache")):
    # Add university to database
    university_dir = os.path.join("..", "cache", university_id)

    university_data = universities[university_id]
    university_data["_id"] = university_id

    if db["universities"].find_one({"_id": university_id}):
        print(f"University {university_id} already in database, skipping")
    else:
        db["universities"].insert_one(university_data)
        print(f"Added university {university_id}")

    # Add university's courses to database
    course_data_file_paths = Path(os.path.join("..", "cache", university_id)).rglob("course_data.json")
    for course_data_file_path in course_data_file_paths:
        with open(course_data_file_path, "r") as file:
            courses = json.load(file)

        for department in courses:
            for course_data in courses[department]:
                course_data["university_id"] = university_id
                course_data["department"] = department
                course_id = "_".join(course_data["number"].replace("-", "_").lower().split(" "))
                course_id = f"{university_id}-{course_id}"
                course_data["_id"] = course_id

                db["courses"].update_one(
                    filter={"_id": course_id},
                    update={"$set": course_data},
                    upsert=True
                )
                print(f"Added course {course_id}")
