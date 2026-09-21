# Job Finder API & MySQL Search System

A Python-based job search application that fetches job listings from the Arbeitnow Job Board API, cleans and processes the data, stores jobs in MySQL, and allows users to search jobs using SQL.

## Features

- Fetches jobs from a REST API
- Supports API pagination
- Handles API rate limiting
- Handles request timeouts and API errors
- Validates user input
- Cleans HTML job descriptions using BeautifulSoup
- Removes duplicate jobs
- Stores jobs in MySQL
- Prevents duplicate database records using unique job links
- Uses SQL `LIKE` queries for job searching
- Displays matching jobs
- Uses environment variables for database credentials
- Provides `requirements.txt` for dependency installation

## Technologies Used

- Python
- REST API
- Requests
- BeautifulSoup
- MySQL
- mysql-connector-python
- python-dotenv
- SQL
- Git & GitHub

## How It Works

```text
                Arbeitnow Job Board API
                         │
                         ▼
                 Python Requests
                         │
                         ▼
              Fetch Multiple Pages
                         │
                         ▼
                Clean Job Data
              (BeautifulSoup)
                         │
                         ▼
              Remove Duplicates
                         │
                         ▼
                 MySQL Database
                         │
                         ▼
                SQL Search Query
              (Title + Location)
                         │
                         ▼
                 Matching Jobs
                         │
                         ▼
                    Display