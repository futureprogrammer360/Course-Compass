"""curriculum_api_data_downloader.py

Program that downloads data about Duke University courses from Duke University's Curriculum API
"""

from os import path, makedirs, listdir, getenv
import json
import time

import yaml
import requests
from dotenv import load_dotenv

load_dotenv()

with open("config.yaml") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

CACHE_DIR = path.abspath(path.join(
    path.dirname(__file__), "..", "..", "..", "cache",
    path.split(path.dirname(__file__))[-1],
    path.splitext(path.basename(__file__))[0]
))
makedirs(CACHE_DIR, exist_ok=True)

API_KEY = getenv("DUKE_UNIVERSITY_CURRICULUM_API_KEY")
BASE_URL = "https://streamer.oit.duke.edu/curriculum"

valid_curriculum_codes = [code for code_list in config.get("curriculum_codes").values() for code in code_list]


class CurriculumAPIDataDownloader:
    """CurriculumAPIDataDownloader

    Data downloader class that fetches data about Duke University courses from the university's Curriculum API
    """

    def __init__(self):
        self.init_time = time.time()

        self.subjects = []
        self.course_list = {}
        self.course_data = {}
        if "subjects.json" in listdir(CACHE_DIR):
            with open(path.join(CACHE_DIR, "subjects.json"), "r") as file:
                self.subjects = json.load(file)
        if "course_list.json" in listdir(CACHE_DIR):
            with open(path.join(CACHE_DIR, "course_list.json"), "r") as file:
                self.course_list = json.load(file)
        if "course_data.json" in listdir(CACHE_DIR):
            with open(path.join(CACHE_DIR, "course_data.json"), "r") as file:
                self.course_data = json.load(file)

        self.courses_with_data = []
        self.crse_id_offer_nbr_and_course_number_mapping = {}
        if "courses_with_data.json" in listdir(CACHE_DIR):
            with open(path.join(CACHE_DIR, "courses_with_data.json"), "r") as file:
                self.courses_with_data = json.load(file)
        if "crse_id_offer_nbr_and_course_number_mapping.json" in listdir(CACHE_DIR):
            with open(path.join(CACHE_DIR, "crse_id_offer_nbr_and_course_number_mapping.json"), "r") as file:
                self.crse_id_offer_nbr_and_course_number_mapping = json.load(file)

    def run(self):
        """
        1. Get a list of subjects
        2. Get a list of courses in each subject
        3. Get detailed data of each course
        4. Link cross-listed courses
        """
        if not self.subjects:
            self.get_subjects()

        for subject in self.subjects:
            if subject["code"] not in self.course_list:
                self.get_course_list(subject)

        try:
            self.get_batch_of_course_data(config.get("curriculum_api_data_downloader_batch_size"))
        except Exception as e:
            print(f"Exception raised: {e}")

        if not self.crse_id_offer_nbr_and_course_number_mapping:
            self.link_crse_id_and_crse_offer_nbr_with_course_number_and_index()

        self.link_cross_listed_courses()

        with open(path.join(CACHE_DIR, "subjects.json"), "w") as file:
            json.dump(self.subjects, file, indent=2)
        with open(path.join(CACHE_DIR, "course_list.json"), "w") as file:
            json.dump(self.course_list, file, indent=2)
        with open(path.join(CACHE_DIR, "course_data.json"), "w") as file:
            json.dump(self.course_data, file, indent=2)
        with open(path.join(CACHE_DIR, "courses_with_data.json"), "w") as file:
            json.dump(self.courses_with_data, file, indent=2)
        with open(path.join(CACHE_DIR, "crse_id_offer_nbr_and_course_number_mapping.json"), "w") as file:
            json.dump(self.crse_id_offer_nbr_and_course_number_mapping, file, indent=2)

    def get_elapsed_time(self):
        return time.time() - self.init_time

    def get_subjects(self):
        """Get list of subjects"""
        print("Getting subjects")

        url = f"{BASE_URL}/list_of_values/fieldname/SUBJECT?access_token={API_KEY}"
        response = requests.get(url)
        data = response.json()

        self.subjects = data["scc_lov_resp"]["lovs"]["lov"]["values"]["value"]

    def get_course_list(self, subject: dict):
        """Get list of courses in the given subject"""
        subject_code = subject["code"]
        subject_desc = subject["desc"]
        print(f"Getting {subject_code} course list")

        url = f"{BASE_URL}/courses/subject/{subject_code} - {subject_desc}?access_token={API_KEY}"
        response = requests.get(url)
        if response.status_code != 200:
            print(f" - Response status code: {response.status_code}, skipping")
            self.course_list[subject_code] = []
            return
        data = response.json()

        course_summaries = data["ssr_get_courses_resp"]["course_search_result"]["subjects"]["subject"]["course_summaries"]
        if course_summaries is not None:
            course_summary = course_summaries["course_summary"]
            if type(course_summary) == dict:  # There is only 1 course in list
                self.course_list[subject_code] = [course_summary]
            elif type(course_summary) == list:  # There are multiple courses in list
                self.course_list[subject_code] = course_summary
        else:
            print(" - No course list available")
            self.course_list[subject_code] = []

    def get_course_data(self, course_info: dict):
        """Get the detailed data of a course given the course info taken from course list"""
        crse_id = course_info["crse_id"]
        crse_offer_nbr = course_info["crse_offer_nbr"]
        print(f"Getting data for course (crse_id: {crse_id}, crse_offer_nbr: {crse_offer_nbr})")

        # Use data from course list as fallback if course data is not available
        crse_data = {
            "title": course_info["course_title_long"],
            "number": f"{course_info['subject'].strip()} {course_info['catalog_nbr'].strip()}",
            "crse_id": course_info["crse_id"],
            "crse_offer_nbr": course_info["crse_offer_nbr"],
            "cross_listed_as": []
        }

        url = f"{BASE_URL}/courses/crse_id/{crse_id}/crse_offer_nbr/{crse_offer_nbr}?access_token={API_KEY}"
        response = requests.get(url)
        if response.status_code != 200:
            print(f" - Response status code: {response.status_code}, using data from course list")
        else:
            data = response.json()
            data = data["ssr_get_course_offering_resp"]["course_offering_result"]
            if "course_offering" in data:
                data = data["course_offering"]

                crse_data["title"] = data["course_title_long"]
                crse_data["number"] = f"{data['subject'].strip()} {data['catalog_nbr'].strip()}"
                crse_data["codes"] = []
                crse_data["description"] = data["descrlong"]
                crse_data["prerequisites"] = data["rqrmnt_group_descr"]
                crse_data["typically_offered"] = data["ssr_crse_typoff_cd_lov_descr"]
                crse_data["cross_listed_as"] = []
                crse_data["crse_id"] = data["crse_id"]
                crse_data["crse_offer_nbr"] = data["crse_offer_nbr"]

                # Determine curriculum codes
                course_attributes_data = data["course_attributes"]
                if course_attributes_data is None:  # There are no course attributes
                    pass
                elif type(course_attributes_data["course_attribute"]) == dict:  # There is only 1 course attribute
                    course_attribute = course_attributes_data["course_attribute"]
                    if course_attribute["crse_attr_value"] in valid_curriculum_codes:
                        crse_data["codes"].append(course_attribute["crse_attr_value"])
                elif type(course_attributes_data["course_attribute"]) == list:  # There are multiple course attributes
                    for course_attribute in course_attributes_data["course_attribute"]:
                        if course_attribute["crse_attr_value"] in valid_curriculum_codes:
                            crse_data["codes"].append(course_attribute["crse_attr_value"])
            else:
                print(f" - No course data available, using data from course list")

        subject = course_info["subject"]
        if subject not in self.course_data:
            self.course_data[subject] = []
        self.course_data[subject].append(crse_data)

    def get_batch_of_course_data(self, batch_size=10):
        """Get data of a batch of courses and maintain record of the courses already with fetched data"""
        scrape_count = 0
        for subject_course_list in self.course_list.values():
            for course_info in subject_course_list:
                crse_id = course_info["crse_id"]
                crse_offer_nbr = course_info["crse_offer_nbr"]
                if f"{crse_id}-{crse_offer_nbr}" not in self.courses_with_data:
                    print(f"{scrape_count + 1}: ", end="")
                    self.get_course_data(course_info)
                    self.courses_with_data.append(f"{crse_id}-{crse_offer_nbr}")
                    scrape_count += 1
                    if scrape_count >= batch_size:
                        return

    def link_cross_listed_courses(self):
        """Link cross-listed-as courses

        Each course listing returned by the Curriculum API has crse_id and crse_offer_nbr fields
        Course listings with the same crse_id but different crse_offer_nbr values are the same course cross-listed with different numbers
        When a course is found with a crse_offer_nbr value that is not 1, it implies there is at least 1 cross-listing for the course
        """
        print("Linking cross-listed courses")
        all_courses = [course for subject_courses in self.course_data.values() for course in subject_courses]
        for course in all_courses:
            crse_id = course["crse_id"]
            crse_offer_nbr = int(course["crse_offer_nbr"])
            course_number = course["number"]
            if crse_offer_nbr > 1:
                for i in range(1, crse_offer_nbr):
                    if f"{crse_id}-{i}" in self.crse_id_offer_nbr_and_course_number_mapping:
                        cross_listed_course_number, index = self.crse_id_offer_nbr_and_course_number_mapping[f"{crse_id}-{i}"]
                        subject = cross_listed_course_number.split(" ")[0]

                        # Add course (of outer loop) to the cross_listed_as list of the cross-listed class (with crse_offer_nbr of i in inner loop)
                        self.course_data[subject][index]["cross_listed_as"].append(course_number)
                        self.course_data[subject][index]["cross_listed_as"] = list(set(self.course_data[subject][index]["cross_listed_as"]))

                        # Add the cross-listed class (with crse_offer_nbr of i in inner loop) to the cross_listed_as list of course (of outer loop)
                        course["cross_listed_as"].append(cross_listed_course_number)
                        course["cross_listed_as"] = list(set(course["cross_listed_as"]))

    def link_crse_id_and_crse_offer_nbr_with_course_number_and_index(self):
        """Create a dictionary mapping (crse_id and crse_offer_nbr) to (course number and course's index in its subject's list of courses)"""
        print("Linking crse_id and crse_offer_nbr with course numbers and indices")
        for subject_courses in self.course_data.values():
            for i, course in enumerate(subject_courses):
                crse_id = course["crse_id"]
                crse_offer_nbr = course["crse_offer_nbr"]
                course_number = course["number"]
                self.crse_id_offer_nbr_and_course_number_mapping[f"{crse_id}-{crse_offer_nbr}"] = (course_number, i)


if __name__ == "__main__":
    data_downloader = CurriculumAPIDataDownloader()
    data_downloader.run()
    print(f"Number of courses with data: {len(data_downloader.courses_with_data)}")
    print(f"Time elapsed: {data_downloader.get_elapsed_time():.2f} seconds")
