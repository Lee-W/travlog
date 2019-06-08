# -*- coding: utf-8 -*- #
from __future__ import unicode_literals
from functools import partial

PATH = 'content'

# Blog Conf
AUTHOR = 'Lee-W'
SITENAME = 'Otaku Travels'
SITEURL = 'http://localhost:8000'
DISQUS_SITENAME = "lee-w-travlog"
SITETITLE = AUTHOR
SITELOGO = None
BROWSER_COLOR = '#333333'

# Locale
TIMEZONE = 'Asia/Taipei'
DEFAULT_LANG = 'zh-tw'
DEFAULT_DATE_FORMAT = '%Y/%m/%d - %a'

# Page Setting
MAIN_MENU = True
DEFAULT_PAGINATION = 10
MENUITEMS = (
    ('Archives', '/archives.html'),
    ('Categories', '/categories.html'),
)
DIRECT_TEMPLATES = ('index', 'categories', 'authors', 'archives')
# SUMMARY_MAX_LENGTH = 0

# Content Setting
DEFAULT_CATEGORY = 'Travel'
ARTICLE_URL = 'posts/{category}/{date:%Y}/{date:%m}/{slug}'
ARTICLE_SAVE_AS = 'posts/{category}/{date:%Y}/{date:%m}/{slug}/index.html'
STATIC_PATHS = ['images', 'static']

# Theme Setting
THEME = 'theme/pelican-clean-blog'
JINJA_ENVIRONMENT = {
    'extensions': ['jinja2.ext.i18n'],
}
EXTRA_PATH_METADATA = {
    'images': {'path': 'images'},
}
PYGMENTS_STYLE = 'default'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Social widget
SOCIAL = (('Linkedin', 'http://tw.linkedin.com/in/clleew'),
          ('GitHub', 'http://github.com/Lee-W'),
          ('Gitlab', 'https://gitlab.com/Lee-W'),
          ('Twitter', 'https://twitter.com/clleew'),
          ('RSS', '//lee-w.github.io/feeds/all.atom.xml'),)

# Markdown extension
MARKDOWN = {
    'extension_configs': {
        'markdown.extensions.extra': {},
        'markdown.extensions.codehilite': {'css_class': 'highlight'},
        'markdown.extensions.nl2br': {},
        # 'del_ins': {},
        'toc': {},
    },
    'output_format': 'html5'
}

# Plugin-setting
PLUGIN_PATHS = ['pelican-plugins']
PLUGINS = [
    'another_read_more_link',
    'neighbors', 'share_post', 'i18n_subsites', 'tipue_search',
]
ANOTHER_READ_MORE_LINK = ''

JINJA_FILTERS = {
    'sort_by_article_count': partial(
        sorted,
        key=lambda x: len(x[1]),
        reverse=True
    )
}
