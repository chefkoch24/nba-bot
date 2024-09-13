import abc
import os
import time
import typing
from datetime import datetime

from dotenv import load_dotenv
from selenium.common import TimeoutException, NoSuchElementException
import nba_api.live.nba.endpoints as nba
# Set up Chrome options for headless mode
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from utils import get_scrape_date, get_game_id, find_elements_with_retry, find_element_with_retry, save_json, \
    write_json_to_s3, str2bool

load_dotenv()

IS_SERVER = False  #str2bool(os.getenv('IS_SERVER'))
BUCKET_NAME = os.getenv("BUCKET_NAME")
BINARY_LOCATION = os.getenv("BINARY_LOCATION")

class Extractor(abc.ABC):

    def __init__(self, base_url: str = 'https://www.nba.com/games?date='):
        self.base_url = base_url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.chrome_options = webdriver.ChromeOptions()
        # Set up Selenium with Chrome WebDriver and headless mode
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("window-size=2560x1440")
        self.chrome_options.add_argument("--remote-debugging-port=9222")

    def extract_on_website(self, date, scrape_date) -> (typing.Dict, str):
        raise NotImplementedError

    def extract(self, date):
        scrape_date = get_scrape_date(date)
        if IS_SERVER:
            self.driver = webdriver.Chrome(service=ChromeService(executable_path="/opt/chromedriver"),
                                           options=self.chrome_options)
            #driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=self.chrome_options)
        else:
            if BINARY_LOCATION is not None:
                self.chrome_options.binary_location = BINARY_LOCATION
                self.driver = webdriver.Chrome(options=self.chrome_options)
            else:
                service = ChromeService(executable_path=ChromeDriverManager().install())
                service.command_line_args().append('--verbose')
                self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
        try:
            # Find elements based on their class names
            self.extract_on_website(date, scrape_date)
        except TimeoutException:
            print("Timeout occurred")  # Handle timeout exception
        finally:
            self.driver.quit()


class NBAExtractor(Extractor):
    def extract_on_website(self, date, scrape_date):
        self.driver.get(self.base_url + scrape_date)
        time.sleep(3)
        try:
            elements = find_elements_with_retry(self.driver, By.CSS_SELECTOR, value='[class^="GameCard"]')
            game_links = [e.get_attribute('href') for e in elements if e.get_attribute('href') is not None]
            game_ids = []
            game_stories = []
            for game_link in tqdm(game_links):
                self.driver.get(game_link)
                time.sleep(1)
                game_ids.append(get_game_id(game_link))
                try:
                    # Attempt to find the game story element with retry logic
                    story = find_element_with_retry(self.driver, By.CSS_SELECTOR, '[class^="GameStory"]')
                    if story:
                        game_stories.append(story.text)
                    else:
                        game_stories.append(
                            "Game postponed")  # Handle case where game story element is not found after retry
                except NoSuchElementException:
                    game_stories.append("No game story found")  # Handle case where game story element is not found
            self.driver.quit()
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
    def extract_on_website(self, date, scrape_date):
        self.driver.get(self.base_url)
        time.sleep(3)
        try:
            game_modules = find_elements_with_retry(self.driver, By.CLASS_NAME, "gameModules")
            for game in game_modules:
                h = game.find_elements(By.TAG_NAME, 'header')
                date_str = h[0].get_attribute('aria-label') #"Friday, September 8, 2023"
                # Define the format of the date string including the weekday
                date_format = "%A, %B %d, %Y"
                # Convert the string to a datetime object
                game_date = datetime.strptime(date_str, date_format)
                if date == game_date:
                    game_links = game.find_elements(By.LINK_TEXT, "Gamecast")
                    game_links = [g.get_attribute('href') for g in game_links]
                    game_links = [g.replace('/game/', '/recap/') for g in game_links]
                    for game_link in tqdm(game_links):
                        self.driver.get(game_link)
                        time.sleep(1)
                        try:
                            game_strips = find_elements_with_retry(self.driver, By.CLASS_NAME, "Gamestrip__Team")
                            away_team_str = game_strips[0].find_elements(By.CLASS_NAME, "ScoreCell__TeamName")[0].get_attribute('innerText')
                            away_score_str = game_strips[0].find_elements(By.CLASS_NAME, "Gamestrip__Score")[0].get_attribute('innerText')
                            home_team_str = game_strips[1].find_elements(By.CLASS_NAME, "ScoreCell__TeamName")[0].get_attribute(
                                'innerText')
                            home_score_str = game_strips[1].find_elements(By.CLASS_NAME, "Gamestrip__Score")[0].get_attribute(
                                'innerText')
                            game_id = get_game_id(game_link)
                            home_score = int(home_score_str)
                            away_score = int(away_score_str)
                            home_team = f"{home_team_str}"
                            away_team = f"{away_team_str}"
                            story = find_element_with_retry(self.driver, By.CSS_SELECTOR,
                                                            '[class^="Story__Wrapper"]').get_attribute("innerText")
                            if story:
                                game_recap = story
                            elif home_score == 0 and away_score == 0:
                                game_recap = 'Game postponed'
                            else:
                                game_recap = 'Game postponed'
                            folder_path = f"nfl/extracted_data/{scrape_date}"
                            file_path = f'{folder_path}/{game_id}.json'
                            content = {'date': f"{date.day}.{date.month}.{date.year}",
                                       'game_id': game_id,
                                       'home_team': home_team,
                                       'away_team': away_team,
                                       'home_score': home_score,
                                       'away_score': away_score,
                                       'game_recap': game_recap,
                                       'box_score_url': f"https://www.espn.com/nfl/boxscore/_/gameId/{game_id}",
                                       'game_cast_url': game_link
                                       }
                            write_json_to_s3(json_content=content, bucket_name='lastnightscores', key=file_path)
                        except Exception as e:
                            print(e)
                            self.driver.refresh()
                    self.driver.quit()
        except NoSuchElementException:
            print("No GameCard elements found")  # Handle case where GameCard elements are not found
