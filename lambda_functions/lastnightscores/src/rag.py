from openai import OpenAI
import os
from dotenv import load_dotenv
from utils import get_all_data, save_json, get_scrape_date, write_json_to_s3, read_json_from_s3

load_dotenv()
API_KEY = os.getenv("API_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")

class RAG:
    def __init__(self):
        self.client = OpenAI(api_key=API_KEY)

    def generate(self, date):
        scrape_date = get_scrape_date(date)
        for league in ['nba', 'nfl', 'nhl']:
            data = read_json_from_s3(bucket_name=BUCKET_NAME, folder_path=f'{league}/extracted_data/{scrape_date}' )#get_all_data(f'extracted_data/{scrape_date}')#
            for d in data:
                if d['home_score'] != 0 and d['away_score'] != 0:
                    # generate prompt
                    prompt = f"""Summarize this game recap in one paragraph including the most interesting facts 
                    about the game. Do not write in all caps or use paragraphs without rephrasing. 
                    \n {d['game_recap']}"""
                    # request model
                    response = self.client.chat.completions.create(
                        model='gpt-4o',
                        messages=[
                            {"role": "user", "content": prompt},
                                ]
                            )
                    generated_content = response.choices[0].message.content
                else:
                    generated_content = d['game_recap']
                d['generated_content'] = generated_content
                folder_path = f"{league}/generated_data/{scrape_date}"
                #if not os.path.exists(folder_path):
                #    os.makedirs(folder_path)
                file_path = f"{folder_path}/{d['game_id']}.json"
                #save_json(d, file_path)
                write_json_to_s3(json_content=d, bucket_name=BUCKET_NAME, key=file_path)

