import os
from dotenv import load_dotenv
from utils import get_all_data, get_scrape_date, read_json_from_s3
import boto3
from botocore.exceptions import ClientError
load_dotenv()

class Generator:
    def generate(self, date):
        title = date.strftime("%d.%m.%Y")
        scrape_date = get_scrape_date(date)
        directory_path = f'generated_data/{scrape_date}'
        body = ""
        #data = read_json_from_s3(bucket_name='nba-bot', folder_path=directory_path)
        data = get_all_data(directory_path)
        body = ""
        for d in data:
            headline = f"**{d['home_team']} {d['home_score']} - {d['away_score']} {d['away_team']}**  \n"
            game_cast_url = d['game_cast_url']
            game_cast_url = f"[Gamecast]({game_cast_url})"
            box_score_url = d['box_score_url']
            box_score_url = f"[Box Score]({box_score_url})"
            body += headline + d['generated_content'] + " \n\n" + box_score_url + ", " + game_cast_url + "<br>" + "\n\n"

        content = "Title: " + title + "\n"
        content += 'Date: ' + date.strftime('%Y-%m-%d %H:%M') + "\n"
        content += "Category: NBA \n"
        content += body

        if body != '':
            with open(f"website/content/articles/nba-daily-{date.strftime('%Y-%m-%d')}.md", "w") as markdown_file:
                markdown_file.write(content)

