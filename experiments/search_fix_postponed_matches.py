import os
import json
import datetime

from extract_data import Extract
from generator import Generator
from rag import RAG


def check_game_postponed(folder_path):
    # Iterate over each folder and subfolder
    counter = 0
    for root, dirs, files in os.walk(folder_path):
        # Iterate over each file in the current folder
        for file_name in files:
            # Check if the file is a JSON file
            if file_name.endswith('.json'):
                file_path = os.path.join(root, file_name)
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # Check if 'home_score' and 'away_score' are not both zero
                    # and 'game_recap' says 'Game postponed'
                    if (data.get('home_score', 0) != 0 or data.get('away_score', 0) != 0) \
                            and data.get('game_recap', '').lower() == 'game postponed':
                        counter+= 1
                        print(f"File: {file_path}")
                        print("Condition met:")
                        print(f"home_score: {data.get('home_score', 0)}, away_score: {data.get('away_score', 0)}")
                        print(f"game_recap: {data.get('game_recap', '')}\n")
                        middle_path = str(file_path).split('/')[1]
                        year, month, day = middle_path.split("-")
                        scrape_date = datetime.date(year=int(year), month=int(month), day=int(day))
                        extractor = Extract()
                        extractor.extract(scrape_date)
                        rag = RAG()
                        rag.generate(scrape_date)
                        scrape_date = scrape_date + datetime.timedelta(days=1)
                        g = Generator()
                        g.generate(scrape_date)
    print(counter)


# Path to the extracted_data folder
extracted_data_folder = 'extracted_data'

# Check games in extracted_data folder
check_game_postponed(extracted_data_folder)
