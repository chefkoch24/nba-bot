import os
import time
from selenium import webdriver
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
import nba_api.live.nba.endpoints as nba

# Set up Chrome options for headless mode
from selenium.webdriver.common.by import By
from tqdm import tqdm

from utils import get_scrape_date, get_game_id, find_elements_with_retry, find_element_with_retry, save_json, \
    write_json_to_s3


class Extract:

    def __init__(self):
        self.base_url = 'https://www.nba.com/games?date='
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')  # Enable headless mode

        # Set up Selenium with Chrome WebDriver and headless mode

    def extract(self, date):
        scrape_date = get_scrape_date(date)
        driver = webdriver.Chrome(options=self.chrome_options)
        driver.get(self.base_url + scrape_date)
        time.sleep(3)
        try:
            # Find elements based on their class names
            elements = find_elements_with_retry(driver, By.CSS_SELECTOR, value='[class^="GameCard"]')
            game_links = [e.get_attribute('href') for e in elements if e.get_attribute('href') is not None]
            game_ids = []
            game_stories = []
            for game_link in tqdm(game_links):
                driver.get(game_link)
                time.sleep(1)
                game_ids.append(get_game_id(game_link))
                try:
                    # Attempt to find the game story element with retry logic
                    story = find_element_with_retry(driver, By.CSS_SELECTOR, '[class^="GameStory"]')
                    if story:
                        game_stories.append(story.text)
                    else:
                        game_stories.append(
                            "Game postponed")# Handle case where game story element is not found after retry
                except NoSuchElementException:
                    game_stories.append("No game story found")  # Handle case where game story element is not found
            driver.quit()
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
                            'box_score_url': f"{game_link}/box-score",
                            'game_cast_url': game_link
                            }
                save_json(content, file_path)
                write_json_to_s3(json_content=content, bucket_name='nba-bot', key=file_path)
        except NoSuchElementException:
            print("No GameCard elements found")  # Handle case where GameCard elements are not found
        except TimeoutException:
            print("Timeout occurred")  # Handle timeout exception
        finally:
            driver.quit()


