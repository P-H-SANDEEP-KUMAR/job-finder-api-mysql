import requests
import time
import json
import os
from bs4 import BeautifulSoup
import mysql.connector
from dotenv import load_dotenv

url = "https://www.arbeitnow.com/api/job-board-api"
max_pages = 20
request_timeout = 10

load_dotenv()
mysql_config = {
    "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE")
}
def get_db_connection():
    return mysql.connector.connect(**mysql_config)
def save_jobs_to_mysql(jobs):
    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
    INSERT IGNORE INTO jobs
    (title, company_name, location, link, description)
    VALUES (%s, %s, %s, %s, %s)
"""
    new_jobs = 0
    for job in jobs:
        cursor.execute(query, (
            job["Title"],
            job["Company Name"],
            job["Location"],
            job["Link"],
            job["Description"]
        ))

        if cursor.rowcount == 1:
                new_jobs += 1

    connection.commit()
    cursor.close()
    connection.close()

    skipped_jobs = len(jobs) - new_jobs

    print(f"{new_jobs} new jobs inserted into MySQL.")
    print(f"{skipped_jobs} existing jobs skipped.")
def search_jobs_from_mysql(job_keyword, location_keyword):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT title, company_name, location, link
        FROM jobs
        WHERE title LIKE %s
        AND location LIKE %s
    """

    cursor.execute(query, (
        f"%{job_keyword}%",
        f"%{location_keyword}%"
    ))

    jobs = cursor.fetchall()

    cursor.close()
    connection.close()

    return jobs
def display_mysql_jobs(jobs):
    if not jobs:
        print("No jobs found in MySQL.")
        return

    for job in jobs:
        print("\nTitle:", job["title"])
        print("Company:", job["company_name"])
        print("Location:", job["location"])
        print("Link:", job["link"])
        print("--------------------")
def clean_description(html_description):
    soup = BeautifulSoup(html_description, "html.parser")
    return soup.get_text(" ", strip=True)


def get_jobs(raw_jobs):
    jobs = []
    for job in raw_jobs:
        clean_job = {
            "Title": job.get("title", ""),
            "Company Name": job.get("company_name", ""),
            "Location": job.get("location", ""),
            "Link": job.get("url", ""),
            "Description": clean_description(job.get("description", ""))
        }
        jobs.append(clean_job)
    return jobs


def remove_duplicates(jobs):
    seen_links = set()
    unique_jobs = []
    for job in jobs:
        link = job["Link"]
        if link and link not in seen_links:
            seen_links.add(link)
            unique_jobs.append(job)
    return unique_jobs


def filter_jobs(jobs, job_keyword, location_keyword):
    job_keyword = job_keyword.lower()
    location_keyword = location_keyword.lower()
    filtered_jobs = []
    for job in jobs:
        title_match = job_keyword in job["Title"].lower()
        location_match = location_keyword in job["Location"].lower()
        if title_match and location_match:
            filtered_jobs.append(job)
    return filtered_jobs


def save_jobs(filtered_jobs):
    with open("jobs.txt", "w", encoding="utf-8") as file:
        for job in filtered_jobs:
            text = f"""Title: {job["Title"]}
Company: {job["Company Name"]}
Location: {job["Location"]}
Link: {job["Link"]}
Description: {job["Description"]}
--------------------
"""
            file.write(text)


def save_jobs_json(filtered_jobs):
    with open("jobs.json", "w", encoding="utf-8") as file:
        json.dump(filtered_jobs, file, indent=2, ensure_ascii=False)


def display_jobs(filtered_jobs):
    for job in filtered_jobs:
        print(f"""
Title: {job["Title"]}
Company: {job["Company Name"]}
Location: {job["Location"]}
Link: {job["Link"]}
--------------------
""")


def main():
    print("Job finder started:")
    try:
        session = requests.Session()

        job_keyword = input('enter job_keyword to search: ').strip()
        location_keyword = input('enter location_keyword to search: ').strip()

        if not job_keyword or not location_keyword:
            print("Error: job_keyword and location_keyword cannot be empty.")
            return

        response = session.get(url, timeout=request_timeout)
        response.raise_for_status()
        print("API status: connected successfully (page 1)")

        try:
            data = response.json()
        except ValueError:
            print("Error: API did not return valid JSON. Aborting.")
            return

        next_page = data.get("links", {}).get("next")
        all_jobs = data.get("data", []).copy()
        pages_fetched = 1

        while next_page and pages_fetched < max_pages:
            print("Fetching:", next_page)
            time.sleep(1)

            next_response = session.get(next_page, timeout=request_timeout)

            if next_response.status_code == 429:
                wait_time = int(next_response.headers.get("Retry-After", 5))
                print(f"Rate limited by API. Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                continue

            next_response.raise_for_status()

            try:
                next_data = next_response.json()
            except ValueError:
                print("Warning: received invalid JSON on a page, skipping it.")
                next_page = None
                continue

            all_jobs.extend(next_data.get("data", []))
            next_page = next_data.get("links", {}).get("next")
            pages_fetched += 1
            print(f"API status: page {pages_fetched} fetched successfully")

        print("Total jobs collected:", len(all_jobs))

        clean_jobs = get_jobs(all_jobs)
        unique_jobs = remove_duplicates(clean_jobs)
        print("Unique jobs:", len(unique_jobs))
        save_jobs_to_mysql(unique_jobs)
        mysql_jobs = search_jobs_from_mysql(job_keyword, location_keyword)

        print(f"MySQL matching jobs: {len(mysql_jobs)}")
        display_mysql_jobs(mysql_jobs)

        print("\n----- Search Summary -----")
        print("Job keyword:", job_keyword)
        print("Location keyword:", location_keyword)
        print("Pages fetched:", pages_fetched)
        print("Total jobs collected:", len(all_jobs))
        print("Unique jobs:", len(unique_jobs))
        print("Matching jobs found:", len(mysql_jobs))
        print("---------------------------")

    except requests.exceptions.Timeout:
        print("Error: the request timed out. Check your internet connection and try again.")
    except requests.exceptions.RequestException as msg:
        print("Network/API Error:", msg)
    except KeyError as msg:
        print("Unexpected response format, missing key:", msg)
    except Exception as msg:
        print("Error:", msg)


if __name__ == "__main__":
    main()
