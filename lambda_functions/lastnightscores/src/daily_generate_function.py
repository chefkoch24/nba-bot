import json
import datetime
import os

from extractor import NBAExtractor, NFLExtractor, NHLExtractor
from utils import get_nfl_meta_data
from rag import RAG
from send_email import Email
from generator import Generator


def lambda_handler(event, context):
    scrape_date = datetime.datetime.today() - datetime.timedelta(days=1)
    scrape_date = scrape_date.replace(hour=0, minute=0, second=0, microsecond=0)
    nba_extractor = NBAExtractor(base_url='https://www.nba.com/games?date=')
    nhl_extractor = NHLExtractor(base_url="https://nhl.com/scores")
    season, number_of_week = get_nfl_meta_data(scrape_date)
    nfl_extractor = NFLExtractor(base_url=f"https://www.espn.com/nfl/scoreboard/_/week/{str(number_of_week)}/year/{str(season)}/seasontype/2")
    nba_extractor.extract(scrape_date)
    nfl_extractor.extract(scrape_date)
    nhl_extractor.extract(scrape_date)

    rag = RAG()
    rag.generate(scrape_date)
    g = Generator()
    today = datetime.datetime.today()
    g.generate(today)
    email = Email()
    subject = f"{os.getenv('SITENAME')} - {datetime.datetime.now().strftime('%d.%m.%Y')}"
    email.send_email(subject, os.getenv('RECEIVE_EMAIL'), scrape_date)



    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": f"Finished for {scrape_date}",
            }
        ),
    }