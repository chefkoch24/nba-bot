import datetime
import os
from extract_data import Extract
from generator import Generator
from rag import RAG
from send_email import Email
from dotenv import load_dotenv

load_dotenv()

scrape_date = datetime.datetime.now() - datetime.timedelta(days=1)
#extractor = Extract()
#extractor.extract(scrape_date)
#rag = RAG()
#rag.generate(scrape_date)
#email = Email()
#subject = f"{os.getenv('SITENAME')} - {datetime.datetime.now().strftime('%d.%m.%Y')}"
#email.send_email(subject, os.getenv('RECEIVE_EMAIL'), scrape_date)

g = Generator()
g.generate()