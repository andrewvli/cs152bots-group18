import requests
import zipfile
import os
import sqlite3
import csv

# Step 1: Download the Tranco Top 1 Million Sites List
def download_tranco_list():
    url = 'https://tranco-list.eu/top-1m.csv.zip'
    response = requests.get(url)
    if response.status_code == 200:
        with open('top-1m.csv.zip', 'wb') as file:
            file.write(response.content)
        print("Tranco list download complete.")
    else:
        print(f"Failed to download the file. Status code: {response.status_code}")

# Step 2: Extract the ZIP file
def extract_tranco_list():
    with zipfile.ZipFile('top-1m.csv.zip', 'r') as zip_ref:
        zip_ref.extractall()
        print("Extraction complete.")

# Step 3: Load the data into the SQLite database
def load_tranco_list_to_db():
    # Connect to the database
    conn = sqlite3.connect('mod_db.sqlite')
    cursor = conn.cursor()

    # Create the table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tranco_top_sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rank INTEGER,
            site TEXT NOT NULL
        )
    ''')

    # Load data from CSV and insert into the database
    with open('top-1m.csv', 'r') as f:
        reader = csv.reader(f)
        cursor.executemany('INSERT INTO tranco_top_sites (rank, site) VALUES (?, ?)', reader)

    conn.commit()
    conn.close()
    print("Data loaded into the database.")

# Run the steps
download_tranco_list()
extract_tranco_list()
load_tranco_list_to_db()
