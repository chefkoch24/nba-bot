import os
from datetime import datetime, timedelta

from lambda_functions.lastnightscores.src.extractor import NFLExtractor, NBAExtractor
from lambda_functions.lastnightscores.src.generator import Generator
from lambda_functions.lastnightscores.src.rag import RAG
from lambda_functions.lastnightscores.src.send_email import Email
from lambda_functions.lastnightscores.src.utils import get_nfl_meta_data
nba_extractor = NBAExtractor(base_url="https://www.nba.com/games?date=")
scrape_date = datetime(year=2024, month=9, day=17)
#scrape_date = datetime(year=2024, month=9, day=15)
nba_extractor.extract(scrape_date)
#season, number_of_week = get_nfl_meta_data(scrape_date)
#nfl_extractor = NFLExtractor(base_url=f"https://www.espn.com/nfl/scoreboard/_/week/{str(number_of_week)}/year/{str(season)}/seasontype/2")
#nfl_extractor.extract(scrape_date)

#rag = RAG()
#rag.generate(scrape_date)

#email = Email()
#subject = f"{os.getenv('SITENAME')} - {datetime.now().strftime('%d.%m.%Y')}"
#email.send_email(subject, os.getenv('RECEIVE_EMAIL'), scrape_date)
#today = datetime(year=2024, month=9, day=8)
#g = Generator()
#g.generate(today)

