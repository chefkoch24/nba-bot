import json
import os
import re
import datetime


def open_json(file_path):
    with open(file_path, 'r') as file:
        json_data = json.load(file)
    return json_data


def save_json(content, file_path):
    with open(file_path, 'w') as json_file:
        json.dump(content, json_file, indent=4)


def get_all_data(directory_path):
    json_files = []
    # Check if the directory exists
    if os.path.exists(directory_path) and os.path.isdir(directory_path):
        # Get a list of all files in the directory
        files = os.listdir(directory_path)

        # Read the content of each file
        for file_name in files:
            file_path = os.path.join(directory_path, file_name)
            if os.path.isfile(file_path):
                json_files.append(open_json(file_path))
    else:
        # Directory does not exist, create it
        print(f"The directory '{directory_path}' does not exist. Creating it...")
        os.makedirs(directory_path)
    return json_files


def extract_score(input: str):
    match = re.search(r'\d+', input)
    return str(match.group())


def get_scrape_date(date: datetime.datetime) -> str:
    if date.month < 10:
        month = f'0{date.month}'
    else:
        month = date.month
    if date.day < 10:
        day = f'0{date.day}'
    else:
        day = date.day
    return f'{date.year}{month}{day}'
