import datetime
from lambda_functions.lastnightscores.src.utils import get_scrape_date, read_json_from_s3


def generate_local(date):
    title = date.strftime("%d.%m.%Y")
    scrape_date = get_scrape_date(date - datetime.timedelta(days=1))

    for league in ['nba', 'nfl', 'nhl']:
        directory_path = f'{league}/generated_data/{scrape_date}'
        data = read_json_from_s3(bucket_name='lastnightscores', folder_path=directory_path)
        body = ""
        for d in data:
            headline = f"**{d['home_team']} {d['home_score']} - {d['away_score']} {d['away_team']}**  \n"
            game_cast_url = d['game_cast_url']
            game_cast_url = f"[Gamecast]({game_cast_url})" + '{:target="_blank"}'
            box_score_url = d['box_score_url']
            box_score_url = f"[Box Score]({box_score_url})" + '{:target="_blank"}'
            body += headline + d['generated_content'] + " \n\n" + box_score_url + ", " + game_cast_url + "<br>" + "\n\n"

        content = "Title: " + title + "\n"
        content += 'Date: ' + date.strftime('%Y-%m-%d %H:%M') + "\n"
        content += f"Category: {league.upper()} \n"
        content += f"Slug: {league}-{date.strftime('%Y-%m-%d')} \n"
        content += body
        if body != '':
            filename = f"website/content/articles/{league}-{date.strftime('%Y-%m-%d')}.md"
            with open(filename, "w") as markdown_file:
                markdown_file.write(content)


# Insert the day you want to generate the blogpost for
date = datetime.datetime(2024, 10, 26)
end_date = datetime.datetime(2024, 10, 27)
while date < end_date:
    generate_local(date)
    date += datetime.timedelta(days=1)