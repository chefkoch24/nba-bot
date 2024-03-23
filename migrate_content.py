import datetime
import os
from dotenv import load_dotenv
from lambda_functions.nba_scraper.src import extract_data, rag, utils, generator



load_dotenv()

scrape_date = datetime.datetime(2024, 3, 21)
while scrape_date < datetime.datetime.today() - datetime.timedelta(days=1):
    print(scrape_date)
    generated_path = f'generated_data/{utils.get_scrape_date(scrape_date)}'
    if not os.path.exists(generated_path):
        extractor = extract_data.Extract()
        extractor.extract(scrape_date)
        rag = rag.RAG()
        rag.generate(scrape_date)
    scrape_date = scrape_date + datetime.timedelta(days=1)


