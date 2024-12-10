"""department_course_catalogs_scraper.py

Program that downloads data about Duke University courses from Trinity College of Arts & Sciences department course catalogs (e.g. https://cs.duke.edu/course-catalog)
"""

import re
from os import path, makedirs
import json
from urllib.parse import urljoin

import yaml
import requests
from bs4 import BeautifulSoup

with open("config.yaml") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

CACHE_DIR = path.abspath(path.join(
    path.dirname(__file__), "..", "..", "..", "cache",
    path.split(path.dirname(__file__))[-1],
    path.splitext(path.basename(__file__))[0]
))
makedirs(CACHE_DIR, exist_ok=True)

valid_curriculum_codes = [code for code_list in config.get("curriculum_codes").values() for code in code_list]


class DepartmentCourseCatalogsScraper:
    """DepartmentCourseCatalogsScraper

    Scraper class that downloads data about Duke University courses from Trinity College of Arts & Sciences department course catalogs
    """

    def __init__(self):
        self.course_catalog_urls = {}
        self.course_data = {}

    def run(self):
        """
        1. Get a list of URLs for department course catalogs
        2. From each department course catalog, scrape basic course data (course title, number, curriculum codes, URL)
        3. Visit each course URL and scrape course description
        """
        self.get_course_catalog_urls()

        for department_name in self.course_catalog_urls:
            self.get_course_data(department_name)

        for department_courses in self.course_data.values():
            for course in department_courses:
                self.get_course_description(course)

        with open(path.join(CACHE_DIR, "course_catalog_urls.json"), "w") as file:
            json.dump(self.course_catalog_urls, file, indent=2)
        with open(path.join(CACHE_DIR, "course_data.json"), "w") as file:
            json.dump(self.course_data, file, indent=2)

    def get_course_catalog_urls(self):
        """Get list of URLs to department course catalogs"""
        print("Getting URLs to department course catalogs")

        # Get URLs to department home pages
        department_urls = {}
        response = requests.get(config.get("department_catalog_url"))
        soup = BeautifulSoup(response.content, "html.parser")
        for tr in soup.select("table tr"):
            department_url = tr.select_one("a")["href"]
            department_name = tr.select_one("th").text
            department_urls[department_name] = department_url

        # Get URLs to department course catalogs
        for department_name, department_url in department_urls.items():
            response = requests.get(department_url)
            soup = BeautifulSoup(response.content, "html.parser")
            for li in soup.select("nav > ul > li"):
                if li.select_one("div a").text == "Courses":
                    course_catalog_path = li.select_one("div a")["href"]
                    if course_catalog_path not in ("/course-catalog", "/courses"):
                        course_catalog_path = "/courses"
                    course_catalog_url = urljoin(department_url, course_catalog_path)
                    self.course_catalog_urls[department_name] = course_catalog_url
                    break
            else:
                course_catalog_url = urljoin(department_url, "/courses")
                if requests.get(course_catalog_url).status_code == 200:
                    self.course_catalog_urls[department_name] = course_catalog_url

    def get_course_data(self, department_name: str):
        """From each department course catalog, scrape course data: course number, title, curriculum codes, as well as URL to course description"""
        print(f"Getting {department_name} department course data")

        course_catalog_url = self.course_catalog_urls[department_name]
        self.course_data[department_name] = []

        response = requests.get(course_catalog_url)
        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.select_one("table.tablesaw")
        for tr in table.select("tbody tr"):
            number = re.sub(" +", " ", tr.select("td")[0].text.strip())
            title = re.sub(" +", " ", tr.select("td")[1].text.strip())
            url = tr.select("td")[1].select_one("a")
            if url:
                url = url["href"]
                url = urljoin(course_catalog_url, url)
            codes = tr.select("td")[2].text.split(", ")
            codes = [code.strip() for code in codes if code.strip() in valid_curriculum_codes]

            self.course_data[department_name].append({
                "title": title,
                "number": number,
                "codes": codes,
                "url": url
            })

    def get_course_description(self, course: dict):
        pass


if __name__ == "__main__":
    scraper = DepartmentCourseCatalogsScraper()
    scraper.run()
