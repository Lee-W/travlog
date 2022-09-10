# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

PATH = "content"

# Blog Conf
AUTHOR = "Lee-W"
SITENAME = "Meet people around the world"
SITETITLE = SITENAME
SITEURL = "http://localhost:8000"
SITELOGO = "/images/avatar.jpg"
BROWSER_COLOR = "#333333"
HEADER_COVER = "/images/cover.jpeg"

# comment system
UTTERANCES_REPO = "Lee-W/Lee-W.github.io"
UTTERANCES_LABEL = "blog-comment"
COMMENTS_INTRO = (
    "Do you like this article? What do your tink about it? Leave you comment below"
)

# Locale
TIMEZONE = "Asia/Taipei"
DEFAULT_LANG = "zh-tw"
OG_LOCALE = "zh-tw"
DEFAULT_DATE_FORMAT = "%Y/%m/%d - %a"

# Page Setting
MAIN_MENU = True
DEFAULT_PAGINATION = 10
MENUITEMS = (
    ("About", "/pages/about.html"),
    ("🍿 Review", "/category/review.html"),
    ("Story Ranking", "/pages/story-ranking.html"),
    ("✈️  Travel", "/category/travel.html"),
    ("🥘 Cook", "/category/cook.html"),
    ("衛宮家料理總覽", "/pages/emiya-toc.html"),
    ("🏷️ Tags", "/tags.html"),
    ("🗄️  Archives", "/archives.html"),
)
DISPLAY_PAGES_ON_MENU = False
DISPLAY_CATEGORIES_ON_MENU = False
DIRECT_TEMPLATES = ("index", "categories", "authors", "archives", "tags")

# Content Setting
DEFAULT_CATEGORY = "Travel"
ARTICLE_URL = "posts/{category}/{date:%Y}/{date:%m}/{slug}"
ARTICLE_SAVE_AS = "posts/{category}/{date:%Y}/{date:%m}/{slug}/index.html"
STATIC_PATHS = ["images", "extra"]

# Theme Setting
THEME = "theme/attila"
JINJA_ENVIRONMENT = {"extensions": ["jinja2.ext.i18n"]}
PYGMENTS_STYLE = "default"

# License
CC_LICENSE = {
    "name": "Creative Commons Attribution-ShareAlike",
    "version": "4.0",
    "slug": "by-sa",
}

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Social widget
SOCIAL = (
    ("linkedin", "http://tw.linkedin.com/in/clleew"),
    ("github", "http://github.com/Lee-W"),
    ("twitter", "https://twitter.com/clleew"),
    ("rss", "//travlog.wei-lee.me/feeds/all.atom.xml"),
)

# Markdown extension
MARKDOWN = {
    "extension_configs": {
        "markdown.extensions.extra": {},
        "markdown.extensions.codehilite": {"css_class": "highlight"},
        "markdown.extensions.nl2br": {},
        "toc": {},
        "markdown_del_ins": {},
    },
    "output_format": "html5",
}

# Plugin-setting
PLUGIN_PATHS = ["pelican-plugins"]
PLUGINS = [
    "another_read_more_link",
    "share_post",
    "i18n_subsites",
    "post_stats",
    "render_math",
]
ANOTHER_READ_MORE_LINK = ""
