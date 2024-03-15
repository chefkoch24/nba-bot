import os

from substack.post import Post

from utils import get_all_data, get_scrape_date


class Publish:

    def publish(self, substack, title, body, date):
        user_id = substack.get_user_id()
        scrape_date = get_scrape_date(date)
        directory_path = f'generated_data/{scrape_date}'

        post = Post(
            title=title,
            subtitle="",
            user_id=user_id
        )

        data = get_all_data(directory_path)
        content = []
        for d in data:
            headline = {'content': f"{d['home_team']} {d['home_score']} - {d['away_score']} {d['away_team']}", 'marks': [{'type': "strong"}]}
            content.append({'type': 'paragraph', 'content': headline})

            body = {'content': d['generated_content']}
            content.append({'type': 'paragraph', 'content': body})

            links = {content: [{'content': 'Game Recap', 'marks':[{'type': "link", 'href': d['game_cast_url']}]},
                               {'content': 'Box Score', 'marks': [{'type': "link", 'href': d['box_score_url']}]}
                               ]}
            content.append({'type': 'paragraph', 'content': links})

        post.add({'type': 'paragraph', 'content': content})

        # bolden text
        #post.add({'type': "paragraph",
        #          'content': [{'content': "This is how you "}, {'content': "bolden ", 'marks': [{'type': "strong"}]},
        #                      {'content': "a word."}]})

        # add hyperlink to text
        #post.add({'type': 'paragraph', 'content': [
        #    {'content': "View Link", 'marks': [{'type': "link", 'href': 'https://whoraised.substack.com/'}]}]})


        draft = substack.post_draft(post.get_draft())



        #substack.prepublish_draft(draft.get("id"))

        #substack.publish_draft(draft.get("id"))
