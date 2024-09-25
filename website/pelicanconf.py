AUTHOR = 'LastNightScores'
SITENAME = 'LastNightScores'
SITEURL = ""


PATH = "content"
STATIC_PATHS = ['pages', 'articles']
PAGE_PATHS = ['pages']
ARTICLE_PATHS = ['articles']
THEME = "themes/my-theme/"
TIMEZONE = 'Europe/Berlin'

DEFAULT_LANG = 'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None


MENUITEMS = (
  #  ('Home', '/'),
    ('About', '/pages/about.html'),
)

# Social widget
SOCIAL = (
    ("You can add links in your config file", "#"),
    ("Another social link", "#"),
)


DISPLAY_PAGES_ON_MENU = True

DEFAULT_PAGINATION = 30


# Uncomment following line if you want document-relative URLs when developing
# RELATIVE_URLS = True