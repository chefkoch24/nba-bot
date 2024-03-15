import datetime
import json

import boto3


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

def read_json_from_s3(bucket_name, folder_path):
    """
    Reads all JSON files from a specified folder within an S3 bucket.

    Parameters:
    - bucket_name: String, the name of the S3 bucket.
    - folder_path: String, the folder path within the S3 bucket.

    Returns:
    - List of dictionaries containing JSON content from each file.
    """
    s3 = boto3.client('s3')

    # List all objects in the specified folder
    try:
        response = s3.list_objects(Bucket=bucket_name, Prefix=folder_path)
    except Exception as e:
        print(f"Error listing objects in S3: {e}")
        return []

    # Read JSON content from each file
    json_contents = []
    for obj in response.get('Contents', []):
        try:
            file_content = s3.get_object(Bucket=bucket_name, Key=obj['Key'])['Body'].read().decode('utf-8')
            json_contents.append(json.loads(file_content))
        except Exception as e:
            print(f"Error reading JSON from {obj['Key']}: {e}")

    return json_contents

def download():
    print('downloading')
    date = datetime.datetime(2024, 2, 15)
    title = date.strftime("%d.%m.%Y")
    scrape_date = get_scrape_date(date)
    directory_path = f'generated_data/{scrape_date}'
    data = read_json_from_s3(bucket_name='nba-bot', folder_path=directory_path)
    body = ""
    for d in data:
        headline = f"**{d['home_team']} {d['home_score']} - {d['away_score']} {d['away_team']}**  \n"
        game_cast_url = d['game_cast_url']
        game_cast_url = f"[Gamecast]({game_cast_url})"
        box_score_url = d['box_score_url']
        box_score_url = f"[Box Score]({box_score_url})"
        body += headline + d['generated_content'] + " \n\n" + box_score_url + ", " + game_cast_url + "\n\n"

    content = "Title: " + title + "\n"
    content += 'Date: ' + date.strftime('%Y-%m-%d %H:%M') + "\n"
    content += "Category: NBA \n"
    content += body

    with open(f"content/articles/nba-daily-{date.strftime('%Y-%m-%d')}.md", "w") as markdown_file:
        markdown_file.write(content)