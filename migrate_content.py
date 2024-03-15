import datetime
import os

from extract_data import Extract
from generator import Generator
from rag import RAG
from dotenv import load_dotenv

from utils import get_scrape_date

load_dotenv()

scrape_date = datetime.datetime(2023, 10, 24)
while scrape_date < datetime.datetime.today() - datetime.timedelta(days=1):
    generated_path = f'generated_data/{get_scrape_date(scrape_date)}'
    if not os.path.exists(generated_path):
        extractor = Extract()
        extractor.extract(scrape_date)
        rag = RAG()
        rag.generate(scrape_date)
    g = Generator()
    g.generate(scrape_date)
    scrape_date = scrape_date + datetime.timedelta(days=1)

