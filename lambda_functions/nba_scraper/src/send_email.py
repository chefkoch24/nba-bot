import os
from dotenv import load_dotenv
from lambda_functions.nba_scraper.src.utils  import get_all_data, get_scrape_date, read_json_from_s3
import boto3
from botocore.exceptions import ClientError
load_dotenv()

class Email:
    def send_email(self, subject, to_email, date):
        scrape_date = get_scrape_date(date)
        directory_path = f'generated_data/{scrape_date}'
        body = ""
        data = read_json_from_s3(bucket_name='nba-scraper', folder_path=directory_path)#get_all_data(directory_path)
        for d in data:
            headline = f"<strong>{d['home_team']} {d['home_score']} - {d['away_score']} {d['away_team']} </strong> <br/>"
            game_cast_url = d['game_cast_url']
            game_cast_url = f'<a href="{game_cast_url}">Game Recap</a>'
            box_score_url = d['box_score_url']
            box_score_url = f'<a href="{box_score_url}">Box Score</a>'
            body = body + headline + d['generated_content'] + "<br/>" + box_score_url + ", " + game_cast_url + "<br/><br/>"
        # This address must be verified with Amazon SES.
        sender = os.getenv('SENDER_EMAIL')
        # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
        AWS_REGION = "eu-central-1"
        # The character encoding for the email.
        CHARSET = "UTF-8"
        # Create a new SES resource and specify a region.
        client = boto3.client('ses', region_name=AWS_REGION)
        # Try to send the email.
        try:
            # Provide the contents of the email.
            response = client.send_email(
                Destination={
                    'ToAddresses': [
                        to_email,
                    ],
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': CHARSET,
                            'Data': body,
                        }
                    },
                    'Subject': {
                        'Charset': CHARSET,
                        'Data': subject,
                    },
                },
                Source=sender,
            )
        # Display an error if something goes wrong.
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            print("Email sent! Message ID:"),
            print(response['MessageId'])
