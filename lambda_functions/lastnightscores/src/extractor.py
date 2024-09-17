import abc
import os
import time
import typing
from datetime import datetime
from selenium.common import TimeoutException, NoSuchElementException, StaleElementReferenceException
import nba_api.live.nba.endpoints as nba
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
from selenium.webdriver import Remote, ChromeOptions as Options
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection as Connection
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from utils import get_scrape_date, get_game_id, find_elements_with_retry, find_element_with_retry, write_json_to_s3, str2bool

load_dotenv()

IS_SERVER = str2bool(os.getenv('IS_SERVER', default=False))
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
        if IS_SERVER:
            if AUTH == 'USER:PASS':
                raise Exception('Provide Scraping Browsers credentials in AUTH ' +
                                'environment variable or update the script.')
            print('Connecting to Browser...')
            server_addr = f'https://{AUTH}@brd.superproxy.io:9515'
            connection = Connection(server_addr, 'goog', 'chrome')
            self.driver = Remote(connection, options=Options())
        else:
            self.chrome_options = webdriver.ChromeOptions()
            # Set up Selenium with Chrome WebDriver and headless mode
            self.chrome_options.add_argument("--headless")
            self.chrome_options.add_argument("--no-sandbox")
            self.chrome_options.add_argument("--disable-extensions")
            self.chrome_options.add_argument("--disable-dev-shm-usage")
            self.chrome_options.add_argument("--disable-gpu")
            self.chrome_options.add_argument("window-size=2560x1440")
            #self.chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
            self.chrome_options.add_argument("--remote-debugging-port=9222")

            if BINARY_LOCATION is not None:
                self.chrome_options.binary_location = BINARY_LOCATION
                self.driver = webdriver.Chrome(options=self.chrome_options)
            else:
                self.chrome_options.add_argument("--disable-extensions")
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
            # Attempt to close the overlay if it exists
            button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.onetrust-close-btn-handler')))
            button.click()
        except NoSuchElementException:
            pass  # Continue if the close button is not found
        try:
            time.sleep(3)
            elements = find_elements_with_retry(self.driver, By.CSS_SELECTOR, '[class^="GameCard"]')
            game_links = [e.get_attribute('href') for e in elements if e.get_attribute('href') is not None]
            game_ids = [get_game_id(g) for g in game_links]
            game_stories = []
            for game_id in tqdm(game_ids):
                time.sleep(3)
                element = find_elements_with_retry(self.driver, By.XPATH, f'//*[@data-content-id="{game_id}"]')[1]
                element.click()
                time.sleep(3)
                try:
                    # Attempt to find the game story element with retry logic
                    story = find_element_with_retry(self.driver, By.CSS_SELECTOR, '[class^="GameStory"]')
                    if story:
                        game_stories.append(story.text)
                    else:
                        game_stories.append(
                            "Game postponed")  # Handle case where game story element is not found after retry
                    self.driver.back()
                except NoSuchElementException:
                    game_stories.append("No game story found")  # Handle case where game story element is not found
                    self.driver.back()
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
            # Attempt to close the overlay if it exists
            button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.onetrust-close-btn-handler')))
            button.click()
        except NoSuchElementException:
            pass  # Continue if the close button is not found
        try:
            game_modules = find_elements_with_retry(self.driver, By.CLASS_NAME, "gameModules")
            for i, g in enumerate(game_modules):
                game_modules = find_elements_with_retry(self.driver, By.CLASS_NAME, "gameModules")
                game_module = game_modules[i]
                h = game_module.find_elements(By.TAG_NAME, 'header')

                date_str = h[0].get_attribute('aria-label')  # "Friday, September 8, 2023"
                # Define the format of the date string including the weekday
                date_format = "%A, %B %d, %Y"
                # Convert the string to a datetime object
                game_date = datetime.strptime(date_str, date_format)
                if date == game_date:
                    game_elements = game_module.find_elements(By.LINK_TEXT, "Gamecast")
                    game_links = [g.get_attribute('href').replace('/game/', '/recap/') for g in game_elements]
                    game_ids = [get_game_id(g) for g in game_links]
                    for game_id, game_link in tqdm(zip(game_ids, game_links)):
                        try:
                            game_element = find_element_with_retry(self.driver, By.XPATH, f'// *[ @ id = "{game_id}"] / div[2] / a[1]')
                            game_element.click()
                        except Exception as e:
                            print(f"Exception or {game_id}")
                        time.sleep(1)
                        try:
                            navigation_items = find_elements_with_retry(self.driver, By.CLASS_NAME, "Nav__Secondary__Menu__Link")
                            navigation_items[1].click()
                            time.sleep(2)
                            game_strips = find_elements_with_retry(self.driver, By.CLASS_NAME, "Gamestrip__Team")
                            away_team_str = game_strips[0].find_elements(By.CLASS_NAME, "ScoreCell__TeamName")[
                                0].get_attribute('innerText')
                            away_score_str = game_strips[0].find_elements(By.CLASS_NAME, "Gamestrip__Score")[
                                0].get_attribute('innerText')
                            home_team_str = game_strips[1].find_elements(By.CLASS_NAME, "ScoreCell__TeamName")[
                                0].get_attribute(
                                'innerText')
                            home_score_str = game_strips[1].find_elements(By.CLASS_NAME, "Gamestrip__Score")[
                                0].get_attribute(
                                'innerText')
                            home_score = int(home_score_str)
                            away_score = int(away_score_str)
                            home_team = f"{home_team_str}"
                            away_team = f"{away_team_str}"
                            try:
                                story = find_element_with_retry(self.driver, By.CSS_SELECTOR,
                                                                '[class^="Story__Wrapper"]').get_attribute("innerText")
                            except NoSuchElementException:
                                story = None
                            if story:
                                game_recap = story
                            elif home_score == 0 and away_score == 0:
                                game_recap = 'Game postponed'
                            else:
                                game_recap = 'No game story found'
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
                            self.driver.back()
                            time.sleep(1)
                            self.driver.back()
                        except Exception as e:
                            print(e)
                            self.driver.back()
        except NoSuchElementException as e:
            print("No GameCard elements found")
            # Handle case where GameCard elements are not found
        except StaleElementReferenceException as e:
            print("StaleElementReferenceException occurred, retrying...")
        except Exception as e:
            print(e)
