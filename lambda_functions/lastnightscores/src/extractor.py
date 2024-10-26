import abc
import json
import os
import time
import typing
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from selenium.common import TimeoutException, NoSuchElementException, StaleElementReferenceException
import nba_api.live.nba.endpoints as nba
from dotenv import load_dotenv
from tqdm import tqdm
from utils import get_scrape_date, get_game_id, write_json_to_s3, str2bool

load_dotenv()

IS_SERVER = str2bool(os.getenv('IS_SERVER'))
BUCKET_NAME = os.getenv("BUCKET_NAME")
BINARY_LOCATION = os.getenv("BINARY_LOCATION")
AUTH = os.getenv('AUTH', default='USER:PASS')


class Extractor(abc.ABC):

    def __init__(self, base_url: str = 'https://www.nba.com/games?date='):
        self.base_url = base_url

    def extract_on_website(self, date, scrape_date) -> (typing.Dict, str):
        raise NotImplementedError

    def extract(self, date):
        scrape_date = get_scrape_date(date)
        try:
            # Find elements based on their class names
            self.extract_on_website(date, scrape_date)
        except TimeoutException:
            print("Timeout occurred")  # Handle timeout exception


class NBAExtractor(Extractor):
    def extract_on_website(self, date, scrape_date):
        response = requests.get(self.base_url + scrape_date)
        soup = BeautifulSoup(response.content, 'html.parser')
        time.sleep(3)
        try:
            elements = soup.select('[class^="GameCard"]')
            game_links = [e.get('href') for e in elements if e.get('href') is not None]
            game_ids = [get_game_id(g) for g in game_links]
            game_stories = []
            for game_id, game_link in tqdm(zip(game_ids, game_links)):
                time.sleep(3)
                response = requests.get("https://nba.com" + game_link)
                try:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    json_data = soup.select('[id^="__NEXT_DATA__"]')[0].text
                    json_data = json.loads(json_data)
                    headline = json_data['props']['pageProps']['story']['header']['headline']
                    story = " ".join(json_data['props']['pageProps']['story']['content'])
                    story = headline + "\n " + story
                    if story:
                        game_stories.append(story)
                    else:
                        game_stories.append(
                            "Game postponed")  # Handle case where game story element is not found after retry
                except NoSuchElementException:
                    game_stories.append("No game story found")  # Handle case where game story element is not found
            for game_id, game_story, game_link in tqdm(zip(game_ids, game_stories, game_links)):
                box_score = nba.BoxScore(game_id=game_id).get_dict()
                box_score = box_score['game']
                home_team = f"{box_score['homeTeam']['teamCity']} {box_score['homeTeam']['teamName']}"
                away_team = f"{box_score['awayTeam']['teamCity']} {box_score['awayTeam']['teamName']}"
                home_score = box_score['homeTeam']['score']
                away_score = box_score['awayTeam']['score']
                if home_score == 0 and away_score == 0:
                    game_recap = 'Game postponed'
                else:
                    game_recap = game_story
                folder_path = f"nba/extracted_data/{scrape_date}"
                file_path = f'{folder_path}/{game_id}.json'
                content = {'date': f"{date.day}.{date.month}.{date.year}",
                           'game_id': game_id,
                           'home_team': home_team,
                           'away_team': away_team,
                           'home_score': home_score,
                           'away_score': away_score,
                           'game_recap': game_recap,
                           'box_score_url': f"{game_link}/box-score",
                           'game_cast_url': game_link
                           }
                write_json_to_s3(json_content=content, bucket_name=BUCKET_NAME, key=file_path)
        except NoSuchElementException:
            print("No GameCard elements found")  # Handle case where GameCard elements are not found


class NFLExtractor(Extractor):
    def __init__(self, base_url: str):
        super().__init__(base_url)

    def _clean_score(self, text: str) -> str:
        winner_index = text.find('Winner')

        # If 'Winner' is found in the string, slice the string up to its position
        if winner_index != -1:
            cleaned_text = text[:winner_index].strip()
        else:
            cleaned_text = text
        return cleaned_text

    def extract_on_website(self, date, scrape_date):
        headers = {
            'Time-Zone': 'US/Eastern',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

        response = requests.get(self.base_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        time.sleep(3)
        try:
            game_modules = soup.find_all(class_='gameModules')
            for i, game_module in enumerate(game_modules):
                date_headers = game_module.find_all('header')

                date_str = date_headers[0].get('aria-label')  # "Friday, September 8, 2023"
                date_format = "%A, %B %d, %Y"
                game_date = datetime.strptime(date_str, date_format)

                if date == game_date:
                    game_elements = game_module.find_all('a', string='Gamecast')
                    game_links = [g['href'].replace('/game/', '/recap/') for g in game_elements]
                    game_ids = [get_game_id(g) for g in game_links]

                    for game_id, game_link in tqdm(zip(game_ids, game_links)):

                        try:
                            time.sleep(3)
                            response = requests.get("https://espn.com" + game_link, headers=headers)
                            soup = BeautifulSoup(response.content, 'html.parser')
                            game_strips = soup.find_all(class_='Gamestrip__Team')
                            away_team_str = game_strips[0].find(class_='ScoreCell__TeamName').text
                            away_score_str = self._clean_score(game_strips[0].find(class_='Gamestrip__Score').text)
                            home_team_str = game_strips[1].find(class_='ScoreCell__TeamName').text
                            home_score_str = self._clean_score(game_strips[1].find(class_='Gamestrip__Score').text)
                            home_score = int(home_score_str)
                            away_score = int(away_score_str)
                            home_team = f"{home_team_str}"
                            away_team = f"{away_team_str}"

                            try:
                                story = soup.select_one('[class^="Story__Wrapper"]').text
                            except AttributeError:
                                story = None

                            if story:
                                game_recap = story
                            elif home_score == 0 and away_score == 0:
                                game_recap = 'Game postponed'
                            else:
                                game_recap = 'No game story found'

                            folder_path = f"nfl/extracted_data/{scrape_date}"
                            file_path = f'{folder_path}/{game_id}.json'
                            content = {
                                'date': f"{date.day}.{date.month}.{date.year}",
                                'game_id': game_id,
                                'home_team': home_team,
                                'away_team': away_team,
                                'home_score': home_score,
                                'away_score': away_score,
                                'game_recap': game_recap,
                                'box_score_url': f"https://www.espn.com/nfl/boxscore/_/gameId/{game_id}",
                                'game_cast_url': game_link
                            }
                            write_json_to_s3(json_content=content, bucket_name=BUCKET_NAME, key=file_path)
                        except Exception as e:
                            print(f"Something went wrong {e}")
        except NoSuchElementException as e:
            print("No GameCard elements found")
            # Handle case where GameCard elements are not found
        except StaleElementReferenceException as e:
            print("StaleElementReferenceException occurred, retrying...")
        except Exception as e:
            print(e)


class NHLExtractor(Extractor):
    def __init__(self, base_url: str):
        super().__init__(base_url)

    def extract_on_website(self, date, scrape_date):
        headers = {'Time-Zone': 'US/Eastern'}
        url = f"https://api-web.nhle.com/v1/score/{scrape_date}"
        response = requests.get(url, headers=headers)
        content = response.json()
        games = content['games']
        for game in tqdm(games):
            away_abbrev = game['awayTeam']['abbrev']
            home_abbrev = game['homeTeam']['abbrev']
            away_team = self._get_team_name(away_abbrev)
            away_team_url = away_team.lower().replace(" ", "-")
            home_team = self._get_team_name(home_abbrev)
            home_team_url = home_team.lower().replace(" ", "-")
            month = self._get_month(int(scrape_date.split('-')[1]))
            day = scrape_date.split('-')[2]

            game_id = game['id']

            home_score = int(game['homeTeam']['score'])
            away_score = int(game['awayTeam']['score'])
            try:
                content_url = f"https://forge-dapi.d3.nhle.com/v2/content/en-us/stories/{away_team_url}-{home_team_url}-game-recap-{month}-{day}"

                r = requests.get(content_url, headers=headers)
                content = r.json()
                text = [c['content'] for c in content['parts'] if c['type'] == 'markdown']
                headline = content['headline']
                story = headline + "\n " + " \n".join(text)
            except Exception as e:
                print(f"Failed to fetch story for {away_team} ({away_abbrev}) vs {home_team} ({home_abbrev}): {e}")
                story = "No game story found"
            folder_path = f"nhl/extracted_data/{scrape_date}"
            file_path = f'{folder_path}/{game_id}.json'
            data = {
                "date": f"{date.day}.{date.month}.{date.year}",
                "game_id": game_id,
                "home_team": home_team,
                "away_team": away_team,
                "home_score": home_score,
                "away_score": away_score,
                "game_recap": story,
                "box_score_url": game['gameCenterLink'],
                "game_cast_url": f"https://www.nhl.com/news/{away_team_url}-{home_team_url}-game-recap-{month.lower()}-{day}" # game_center_links are 1-indexed
            }
            write_json_to_s3(json_content=data, bucket_name=BUCKET_NAME, key=file_path)





    def _get_team_name(self, abbreviation: str) -> str:
        # abbreviations of all nhl teams
        teams = {
            'ana': 'Anaheim Ducks',
            'ari': 'Arizona Coyotes',
            'bos': 'Boston Bruins',
            'buf': 'Buffalo Sabres',
            'cgy': 'Calgary Flames',
            'car': 'Carolina Hurricanes',
            'chi': 'Chicago Blackhawks',
            'col': 'Colorado Avalanche',
            'cbj': 'Columbus Blue Jackets',
            'dal': 'Dallas Stars',
            'det': 'Detroit Red Wings',
            'edm': 'Edmonton Oilers',
            'fla': 'Florida Panthers',
            'lak': 'Los Angeles Kings',
            'min': 'Minnesota Wild',
            'mtl': 'Montreal Canadiens',
            'nsh': 'Nashville Predators',
            'njd': 'New Jersey Devils',
            'nyi': 'New York Islanders',
            'nyr': 'New York Rangers',
            'ott': 'Ottawa Senators',
            'phi': 'Philadelphia Flyers',
            'pit': 'Pittsburgh Penguins',
            'sjs': 'San Jose Sharks',
            'sea': 'Seattle Kraken',
            'stl': 'St Louis Blues',
            'tbl': 'Tampa Bay Lightning',
            'tor': 'Toronto Maple Leafs',
            'van': 'Vancouver Canucks',
            'vgk': 'Vegas Golden Knights',
            'wsh': 'Washington Capitals',
            'wpg': 'Winnipeg Jets'
        }
        return teams.get(abbreviation.lower(), "Invalid Team")

    def _get_month(self, month: int) -> str:
        months = {
            1: 'January',
            2: 'February',
            3: 'March',
            4: 'April',
            5: 'May',
            6: 'June',
            7: 'July',
            8: 'August',
            9: 'September',
            10: 'October',
            11: 'November',
            12: 'December'
        }
        return months.get(month, "Invalid month")
