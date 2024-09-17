import json
import os
import re
import datetime
import time
from argparse import ArgumentTypeError

import boto3
from dotenv import load_dotenv
from selenium.common import NoSuchElementException, StaleElementReferenceException

load_dotenv()

AWS_PROFILE = os.getenv('AWS_PROFILE')


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



def get_game_id(url: str):
    # Extract digits using regular expression
    digits = re.findall(r'\d+', url)
    # Convert list of strings to integers
    return digits[0]


def get_scrape_date(date: datetime.datetime) -> str:
    if date.month < 10:
        month = f'0{date.month}'
    else:
        month = date.month
    if date.day < 10:
        day = f'0{date.day}'
    else:
        day = date.day
    #return f'{date.year}{month}{day}'
    return f'{date.year}-{month}-{day}'

def find_element_with_retry(driver, by, value, max_retries=100, retry_interval=2, refresh_threshold=5):
        """
        Find the element with retry logic.
        :param driver: Selenium WebDriver instance.
        :param by: The locating mechanism.
        :param value: The value to search for.
        :param max_retries: Maximum number of retries.
        :param retry_interval: Interval between retries.
        :return: The found element or None if not found.
        """
        retries = 0
        refresh_count = 0
        while retries < max_retries:
            try:
                element = driver.find_element(by=by, value=value)
                return element
            except StaleElementReferenceException:
                print("Stale element encountered. Retrying...")
            except NoSuchElementException:
                print("No such element. Retrying...")
            retries += 1
            if retries % refresh_threshold == 0:
                print(f"Refreshing page (attempt {refresh_count + 1})...")
                driver.refresh()
                refresh_count += 1
                time.sleep(retry_interval)  # Add a wait after refreshing the page
        return None

def find_elements_with_retry(driver, by, value, max_retries=100, retry_interval=2, refresh_threshold=5):
        """
        Find the element with retry logic.
        :param driver: Selenium WebDriver instance.
        :param by: The locating mechanism.
        :param value: The value to search for.
        :param max_retries: Maximum number of retries.
        :param retry_interval: Interval between retries.
        :return: The found element or None if not found.
        """
        retries = 0
        refresh_count = 0
        while retries < max_retries:
            try:
                element = driver.find_elements(by=by, value=value)
                return element
            except StaleElementReferenceException:
                print("Stale element encountered. Retrying...")
            retries += 1
            if retries % refresh_threshold == 0:
                print(f"Refreshing page (attempt {refresh_count + 1})...")
                driver.refresh()
                refresh_count += 1
                time.sleep(retry_interval)  # Add a wait after refreshing the page
        return None

def write_json_to_s3(json_content, bucket_name, key):
    """
    Writes JSON content to an S3 bucket.

    Parameters:
    - json_content: Dictionary, the content to be written as JSON.
    - bucket_name: String, the name of the S3 bucket.
    - key: String, the object key (path) within the S3 bucket.

    Returns:
    - None
    """
    session = boto3.Session(profile_name=AWS_PROFILE)
    s3 = session.resource("s3")
    # Convert Python dictionary to JSON string
    json_data = json.dumps(json_content, indent=2)
    s3.Bucket(bucket_name).put_object(Body=json_data, Key=key)



def read_json_from_s3(bucket_name, folder_path):
    """
    Reads all JSON files from a specified folder within an S3 bucket.

    Parameters:
    - bucket_name: String, the name of the S3 bucket.
    - folder_path: String, the folder path within the S3 bucket.

    Returns:
    - List of dictionaries containing JSON content from each file.
    """
    session = boto3.Session(profile_name=AWS_PROFILE)
    s3 = session.resource("s3")

    # List all objects in the specified folder
    try:
        response = []
        for o in s3.Bucket(bucket_name).objects.filter(Prefix=folder_path):
            obj_body = o.get()['Body'].read().decode('utf-8')
            # Parse the JSON content
            try:
                json_content = json.loads(obj_body)
                response.append(json_content)
            except Exception as e:
                print(f"Error reading JSON from {o['Key']}: {e}")
        return response
    except Exception as e:
        print(f"Error listing objects in S3: {e}")
        return []


def create_email_content(date):
    scrape_date = get_scrape_date(date)
    directory_path = f'generated_data/{scrape_date}'
    body = ""
    data = get_all_data(directory_path)
    for d in data:
        headline = f"<strong>{d['home_team']} {d['home_score']} - {d['away_score']} {d['away_team']} </strong> <br/>"
        game_cast_url = d['game_cast_url']
        game_cast_url = f'<a href="{game_cast_url}">ESPN Game</a>'
        box_score_url = d['box_score_url']
        box_score_url = f'<a href="{box_score_url}">Box Score</a>'
        body = body + headline + d['generated_content'] + "<br/>" + box_score_url + ", " + game_cast_url + "<br/><br/>"
    return body

def str2bool(val: str):
    if isinstance(val, bool):
        return val
    if val.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif val.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise ArgumentTypeError('Expected boolean value.')

def get_nfl_meta_data(date: datetime.datetime.date) -> (int, int):
    season = 2024
    start_date = datetime.datetime(year=season, month=9, day=6)
    week_end = start_date + datetime.timedelta(days=7)
    week = 1
    while date >= start_date and date > week_end:
        week += 1
        week_end = week_end + datetime.timedelta(days=7)
    return season, week