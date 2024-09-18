import datetime
import json
from rag import RAG


def lambda_handler(event, context):
    scrape_date = datetime.datetime.now() - datetime.timedelta(days=1)
    rag = RAG()
    rag.generate(scrape_date)
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": f"Generating Finished for {scrape_date}",
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