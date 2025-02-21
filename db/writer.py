"""writer.py

Program that writes data on universities and courses to database
"""

import os
import json
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

with open("data_sources_config.yaml") as file:
    data_sources_config = yaml.load(file, Loader=yaml.FullLoader)

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
    university_data_sources = data_sources_config[university_id]
    course_data_file_paths = [os.path.join("..", "cache", university_id, data_source, "course_data.json") for data_source in university_data_sources]
    for i, course_data_file_path in enumerate(course_data_file_paths):
        print(f"Processing course data from source {university_id}-{i}")
        with open(course_data_file_path, "r") as file:
            courses = json.load(file)

        for department in courses:
            for course_data in courses[department]:
                course_data["university_id"] = university_id
                course_data["department"] = department
                course_data["src"] = i
                course_id = "_".join(course_data["number"].replace("-", "_").lower().split(" "))
                course_id = f"{university_id}-{course_id}"
                course_data["_id"] = course_id

                existing_course = db["courses"].find_one({"_id": course_id})
                if existing_course and existing_course["src"] < i:
                    print(f"Course {course_id} already in database from another source, skipping")
                else:
                    db["courses"].update_one(
                        filter={"_id": course_id},
                        update={"$set": course_data},
                        upsert=True
                    )
                    print(f"Added/updated course {course_id}")
