import datetime
import os

from extract_data import Extract
from generator import Generator
from rag import RAG
from dotenv import load_dotenv

from utils import get_scrape_date

load_dotenv()

scrape_date = datetime.datetime(2024, 3, 18)
while scrape_date < datetime.datetime.today() - datetime.timedelta(days=1):
    print(scrape_date)
    generated_path = f'generated_data/{get_scrape_date(scrape_date)}'
    if not os.path.exists(generated_path):
        extractor = Extract()
        extractor.extract(scrape_date)
        rag = RAG()
        rag.generate(scrape_date)
    g = Generator()
    scrape_date = scrape_date + datetime.timedelta(days=1)
    g.generate(scrape_date) #it expects to scrape the day before


