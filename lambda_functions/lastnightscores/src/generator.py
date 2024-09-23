import datetime
import os
import shutil

from dotenv import load_dotenv
from utils import get_all_data, get_scrape_date, read_json_from_s3
import git
load_dotenv()


BUCKET_NAME = os.getenv("BUCKET_NAME")

class Generator:
    def generate(self, date):
        title = date.strftime("%d.%m.%Y")
        scrape_date = get_scrape_date(date - datetime.timedelta(days=1))
        filenames = []
        self.git_clone_repo()
        for league in ['nba', 'nfl']:
            directory_path = f'{league}/generated_data/{scrape_date}'
            body = ""
            data = read_json_from_s3(bucket_name=BUCKET_NAME, folder_path=directory_path)
            #data = get_all_data(directory_path)
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
                filename = f"/tmp/nba-bot/website/content/articles/{league}-{date.strftime('%Y-%m-%d')}.md"
                filenames.append(filename)
                with open(filename, "w") as markdown_file:
                    markdown_file.write(content)
        self.git_commit_push(filenames)



    def git_clone_repo(self):
        try:
            repo_path = "/tmp/nba-bot"
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)  # Remove the directory if it exists
            self.repo = git.Repo.clone_from(
                url=f"https://{os.getenv('GITHUB_USERNAME')}:{os.getenv('GITHUB_TOKEN')}@github.com/chefkoch24/nba-bot",
                to_path=repo_path
            )
        except Exception as e:
            print(f"Error: {e}")

    def git_commit_push(self, filenames: []):
        try:
            # Add the file to the index
            self.repo.index.add(filenames)

            # Commit the changes
            self.repo.index.commit(f"Added article: {datetime.datetime.today()}")

            # Push the changes to the remote repository
            origin = self.repo.remote(name='origin')
            origin.push(refspec='master:master')
            origin.push()
        except Exception as e:
            print(f"Error: {e}")

