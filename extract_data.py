import os

from bs4 import BeautifulSoup
import requests
import datetime

from tqdm import tqdm

from utils import save_json, extract_score, get_scrape_date, write_json_to_s3


class Extract:

    def __init__(self):
        self.base_url = f'https://www.espn.com/nba/scoreboard/_/date/'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def extract(self, date: datetime.datetime):
        scrape_date = get_scrape_date(date)
        # Send an HTTP request to the URL
        response = requests.get(self.base_url + scrape_date, headers=self.headers)
        game_ids =[]
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content of the page using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            games = soup.find_all(class_='Scoreboard')
            # Print the text content of each paragraph
            for game in games:
                game_ids.append(game.get('id'))
        else:
            print(f"Failed to retrieve the page. Status code: {response.status_code}")
        for game_id in tqdm(game_ids):
            game_url = f'https://www.espn.com/nba/recap/_/gameId/{game_id}'
            response = requests.get(game_url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            game_strip = soup.find(class_='Gamestrip')
            teams = game_strip.find_all('h2')
            home_team = teams[1].text.strip()
            away_team = teams[0].text.strip()
            scores = game_strip.find_all(class_='Gamestrip__Score')
            if len(scores) >= 2:
                home_score = extract_score(scores[1].text)
                away_score = extract_score(scores[0].text)
            else:
                home_score = 0
                away_score = 0
            game_recap = soup.find(class_='Story__Body t__body')
            if game_recap:
                game_recap = game_recap.text.strip().replace('              ', '\n')
            else:
                game_recap = 'Game postponed'
            folder_path = f"extracted_data/{scrape_date}"
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            file_path = f'{folder_path}/{game_id}.json'
            content = {'date': f"{date.day}.{date.month}.{date.year}",
                       'game_id': game_id,
                       'home_team': home_team,
                       'away_team': away_team,
                       'home_score': home_score,
                       'away_score': away_score,
                       'game_recap': game_recap,
                       'box_score_url': f"https://www.espn.com/nba/boxscore/_/gameId/{game_id}",
                       'game_cast_url':f"https://www.espn.com/nba/game/_/gameId/{game_id}"}
            save_json(content, file_path)
            write_json_to_s3(json_content=content, bucket_name='nba-bot', key=file_path)



