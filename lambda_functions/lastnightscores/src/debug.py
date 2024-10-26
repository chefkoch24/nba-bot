import os
import datetime
from datetime import timedelta

from lambda_functions.lastnightscores.src.extractor import NFLExtractor, NBAExtractor, NHLExtractor
from lambda_functions.lastnightscores.src.generator import Generator
from lambda_functions.lastnightscores.src.rag import RAG
from lambda_functions.lastnightscores.src.send_email import Email
from lambda_functions.lastnightscores.src.utils import get_nfl_meta_data

scrape_date = datetime.datetime(2024, 10, 26)
scrape_date = scrape_date - datetime.timedelta(days=1)
scrape_date = scrape_date.replace(hour=0, minute=0, second=0, microsecond=0)

#nhl_extractor = NHLExtractor(base_url="https://nhl.com/scores")
#nhl_extractor.extract(scrape_date)
#nba_extractor = NBAExtractor(base_url='https://www.nba.com/games?date=')
#season, number_of_week = get_nfl_meta_data(scrape_date)
#nfl_extractor = NFLExtractor(
#    base_url=f"https://www.espn.com/nfl/scoreboard/_/week/{str(number_of_week)}/year/{str(season)}/seasontype/2")
#nba_extractor.extract(scrape_date)
#nfl_extractor.extract(scrape_date)
date = datetime.datetime(2024, 10, 7)
end_date = datetime.datetime(2024, 10, 25)
while date < end_date:
    rag = RAG()
    rag.generate(date)
    date += datetime.timedelta(days=1)

#g = Generator()
#today = datetime.datetime.today()
#g.generate(today)
#email = Email()
#subject = f"{os.getenv('SITENAME')} - {datetime.datetime.now().strftime('%d.%m.%Y')}"
#email.send_email(subject, os.getenv('RECEIVE_EMAIL'), scrape_date)

