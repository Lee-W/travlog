# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

PATH = "content"

# Blog Conf
AUTHOR = "Wei Lee"
SITENAME = "Those things no one cares about"
SITETITLE = SITENAME
SITEURL = "http://localhost:8000"
SITELOGO = "/images/avatar.jpg"
BROWSER_COLOR = "#333333"
HEADER_COVER = "/images/cover.jpeg"
DEFAULT_DATE_FORMAT = "%Y/%m/%d - %a"

# Locale
TIMEZONE = "Asia/Taipei"
DEFAULT_LANG = "zh-tw"
OG_LOCALE = "zh-tw"

# utterance (comment system)
UTTERANCES_REPO = "Lee-W/travlog"
UTTERANCES_LABEL = "blog-comment"
COMMENTS_INTRO = (
    "Do you like this article? What do your tink about it? Leave you comment below"
)

# Page Setting
MAIN_MENU = True
DEFAULT_PAGINATION = 10
MENUITEMS = (
    ("Home", "/"),
    ("About", "/pages/about.html"),
    ("🍿 Review", "/category/review.html"),
    ("✈️  Travel", "/category/travel.html"),
    ("🥘 Cook", "/category/cook.html"),
    ("🏷️ Tags", "/tags.html"),
    ("🗄️ Archives", "/archives.html"),
    ("📚 Pages", "/pages/pages.html"),
    ("🔍 Search", "/pages/search.html"),
)
SHOW_PAGES_ON_MENU = False
SHOW_CATEGORIES_ON_MENU = False
SHOW_TAGS_IN_ARTICLE_SUMMARY = True
DIRECT_TEMPLATES = ("index", "categories", "authors", "archives", "tags")
PAGEFIND_ENABLED = True
CSS_OVERRIDE = ["statics/css/blog.css"]

# Content Setting
DEFAULT_CATEGORY = "Travel"
ARTICLE_URL = "posts/{category}/{date:%Y}/{date:%m}/{slug}"
ARTICLE_SAVE_AS = "posts/{category}/{date:%Y}/{date:%m}/{slug}/index.html"
STATIC_PATHS = ["images", "extra", "statics"]

# Theme Setting
THEME = "theme/attila"
JINJA_ENVIRONMENT = {"extensions": ["jinja2.ext.i18n"]}
PYGMENTS_STYLE = "default"
SHOW_ARTICLE_MODIFIED_TIME = True
CATEGORIES_URL = "category"
TAGS_URL = "tag"
AUTHOR_META = {
    "wei lee": {
        "image": "/images/avatar.jpg",
    }
}

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
        "markdown.extensions.toc": {"toc_depth": "1-3"},
        "markdown_del_ins": {},
    },
    "output_format": "html5",
}

# Plugin-setting
PLUGIN_PATHS = ["pelican-plugins"]
PLUGINS = [
    "another_read_more_link",
    "i18n_subsites",
    "post_stats",
    "pelican.plugins.render_math",
    "pelican.plugins.share_post",
    "pelican.plugins.seo",
    "series",
]
ANOTHER_READ_MORE_LINK = ""
SEO_REPORT = True  # SEO report is enabled by default
SEO_ENHANCER = True  # SEO enhancer is disabled by default
SEO_ENHANCER_OPEN_GRAPH = True  # Subfeature of SEO enhancer
SEO_ENHANCER_TWITTER_CARDS = True  # Subfeature of SEO enhancer
