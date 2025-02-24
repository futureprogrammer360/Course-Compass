# Course Compass: College Class Info Lookup

This repository stores the code for **Course Compass**, the search engine for university course data.

The application currently supports access to the data of 13,000+ courses from the following universities:

* Duke University

## Installation

The Chrome extension can be installed from the Chrome Web Store [here](https://chromewebstore.google.com/detail/course-compass-college-cl/ggbeffomhadaajdnnkdhgmlagbggpodf).

## Technologies Used

* Data scrapers: **Python** is used to scrape course details from websites and download course data from APIs.
* Database: Course data is stored in a **MongoDB** database deployed on MongoDB Atlas.
* API: A RESTful API is created in Python using the **FastAPI** framework to efficiently fetch and query data from the database. The API is containerized using **Docker**. A Docker container image is stored on **Amazon Elastic Container Registry** (ECR). The API image stored on ECR is then deployed through an **AWS Lambda** function.
* Extension: The Chrome extension frontend is developed using the **React** framework and built using **Vite**.
