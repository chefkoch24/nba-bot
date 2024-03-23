
import datetime
import json
import os

from send_email import Email
from generator import Generator


def lambda_handler(event, context):
    scrape_date = datetime.datetime.now() - datetime.timedelta(days=1)
    email = Email()
    subject = f"{os.getenv('SITENAME')} - {datetime.datetime.now().strftime('%d.%m.%Y')}"
    email.send_email(subject, os.getenv('RECEIVE_EMAIL'), scrape_date)
    today = datetime.datetime.today()
    g = Generator()
    g.generate(today)
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