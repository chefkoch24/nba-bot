import json
import datetime
from extractor import NBAExtractor, NFLExtractor
from utils import get_nfl_meta_data


def lambda_handler(event, context):
    scrape_date = datetime.datetime.now() - datetime.timedelta(days=1)
    nba_extractor = NBAExtractor()
    season, number_of_week = get_nfl_meta_data(scrape_date)
    nfl_extractor = NFLExtractor(base_url=f"https://www.espn.com/nfl/scoreboard/_/week/{str(number_of_week)}/year/{str(season)}/seasontype/2")
    nba_extractor.extract(scrape_date)
    nfl_extractor.extract(scrape_date)
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": f"Scraping Finished for {scrape_date}",
            }
        ),
    }


def generate_response(response_code, message):
    return {
        "statusCode": response_code,
        "body": message,
        "headers": {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
            "Access-Control-Allow-Methods": "GET"
        }
    }