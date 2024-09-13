import os
from datetime import datetime, timedelta

from extractor import NFLExtractor, NBAExtractor
from lambda_functions.nba_scraper.src.generator import Generator
from lambda_functions.nba_scraper.src.rag import RAG
from lambda_functions.nba_scraper.src.send_email import Email


def get_nfl_meta_data(date: datetime.date) -> (int, int):
    season = 2024
    start_date = datetime(year=season, month=9, day=6)
    week_end = start_date + timedelta(days=7)
    week = 1
    while date >= start_date and date > week_end:
        week += 1
        week_end = week_end + timedelta(days=7)
    return season, week


nba_extractor = NBAExtractor(base_url="https://www.nba.com/games?date=")
#scrape_date = datetime.datetime.now() - datetime.timedelta(days=1)
scrape_date = datetime(year=2024, month=9, day=7)
#nba_extractor.extract(scrape_date)
season, number_of_week = get_nfl_meta_data(scrape_date)
nfl_extractor = NFLExtractor(base_url=f"https://www.espn.com/nfl/scoreboard/_/week/{str(number_of_week)}/year/{str(season)}/seasontype/2")
nfl_extractor.extract(scrape_date)

#rag = RAG()
#rag.generate(scrape_date)

email = Email()
#subject = f"{os.getenv('SITENAME')} - {datetime.now().strftime('%d.%m.%Y')}"
#email.send_email(subject, os.getenv('RECEIVE_EMAIL'), scrape_date)
today = datetime(year=2024, month=9, day=8)
g = Generator()
g.generate(today)

