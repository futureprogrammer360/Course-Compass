"""department_course_catalogs_scraper.py

Program that downloads data about Duke University courses from Trinity College of Arts & Sciences department course catalogs (e.g. https://cs.duke.edu/course-catalog) and additional course catalogs with similar table format (listed in config.yaml)
"""

import re
from os import path, makedirs, listdir
import json
from urllib.parse import urljoin
import time

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
        self.init_time = time.time()

        self.course_catalog_urls = {}
        self.course_data = {}
        if "course_catalog_urls.json" in listdir(CACHE_DIR):
            with open(path.join(CACHE_DIR, "course_catalog_urls.json"), "r") as file:
                self.course_catalog_urls = json.load(file)
        if "course_data.json" in listdir(CACHE_DIR):
            with open(path.join(CACHE_DIR, "course_data.json"), "r") as file:
                self.course_data = json.load(file)

        self.courses_with_scraped_description = []
        if "courses_with_scraped_description.json" in listdir(CACHE_DIR):
            with open(path.join(CACHE_DIR, "courses_with_scraped_description.json"), "r") as file:
                self.courses_with_scraped_description = json.load(file)

    def run(self):
        """
        1. Get a list of URLs for department course catalogs
        2. From each department course catalog, scrape basic course data (course title, number, curriculum codes, URL)
        3. Visit each course URL and scrape course description
        """
        if not self.course_catalog_urls:
            self.get_course_catalog_urls()
            # Add additional course catalogs not scraped from department pages
            for additional_course_catalog_name, additional_course_catalog_url in config.get("additional_course_catalog_urls").items():
                self.course_catalog_urls[additional_course_catalog_name] = additional_course_catalog_url

        if not self.course_data:
            for department_name in self.course_catalog_urls:
                self.get_course_data(department_name)

        try:
            self.scrape_batch_of_course_descriptions(config.get("course_descriptions_scraper_batch_size"))
        except Exception as e:
            print(f"Exception raised: {e}")

        with open(path.join(CACHE_DIR, "course_catalog_urls.json"), "w") as file:
            json.dump(self.course_catalog_urls, file, indent=2)
        with open(path.join(CACHE_DIR, "course_data.json"), "w") as file:
            json.dump(self.course_data, file, indent=2)
        with open(path.join(CACHE_DIR, "courses_with_scraped_description.json"), "w") as file:
            json.dump(self.courses_with_scraped_description, file, indent=2)

    def get_elapsed_time(self):
        return time.time() - self.init_time

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

    def get_course_description(self, course_data: dict) -> dict:
        """Given basic course data (including URL, if available), visit course page and scrape course description, prerequisites, cross-listed course numbers, and typical offered terms"""
        print(f"Getting course description for {course_data['number']}")
        if course_data.get("url") is None:
            return course_data

        url = course_data["url"]
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        section_section = soup.select_one("div#main div#content section.section")
        div = section_section.select_one("section > div#block-tts-sub-content")
        if div is None:
            div = section_section.select_one("div#block-tts-labs-ctrs-content")
        left_div, right_div = div.select("div.content > div > div")

        description_divs = left_div.find_all("div", recursive=False)
        if description_divs:
            description = "\n".join([description_div.text for description_div in description_divs])
        else:
            description = None

        prerequisites = None
        prerequisites_label = left_div.find("h4", string="Prerequisites")
        if prerequisites_label is not None:
            prerequisites = prerequisites_label.find_next_sibling().text.strip()

        typically_offered_label = right_div.find("h5", string="Typically Offered", recursive=False)
        typically_offered = None
        if typically_offered_label is not None:
            typically_offered = typically_offered_label.find_next_sibling(string=True).strip()

        cross_listed_as = []
        for div in right_div.select("div.field"):
            label = div.select_one("h5")
            if label is not None:
                label = label.text
                lis = div.select("ul > li")
                if label == "Cross-Listed As":
                    cross_listed_as = [li.text.strip() for li in lis]

        course_data["description"] = description
        course_data["prerequisites"] = prerequisites
        course_data["typically_offered"] = typically_offered
        course_data["cross_listed_as"] = cross_listed_as

        return course_data

    def scrape_batch_of_course_descriptions(self, batch_size=10):
        """Scrape descriptions of a batch of courses and maintain record of the courses that have been scraped"""
        scrape_count = 0
        for department_courses in self.course_data.values():
            for course_data in department_courses:
                course_number = course_data["number"]
                if course_number not in self.courses_with_scraped_description:
                    print(f"{scrape_count + 1}: ", end="")
                    self.get_course_description(course_data)
                    self.courses_with_scraped_description.append(course_data["number"])
                    scrape_count += 1
                    if scrape_count >= batch_size:
                        return
                    time.sleep(config.get("sleep_time_sec"))


if __name__ == "__main__":
    scraper = DepartmentCourseCatalogsScraper()
    scraper.run()
    print(f"Number of courses with scraped description: {len(scraper.courses_with_scraped_description)}")
    print(f"Time elapsed: {scraper.get_elapsed_time():.2f} seconds")
