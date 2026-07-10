from pelican.themes import attila

HOST = "travlog.wei-lee.me"

# ----common between blogs----
PATH = "content"

# Blog Conf
AUTHOR = "Wei Lee"
SITEURL = "http://localhost:8000"
STATIC_SITEURL = SITEURL
SITELOGO = "/images/avatar.jpg"
BROWSER_COLOR = "#333333"
HEADER_COVER = "images/cover.jpeg"
SITE_DESCRIPTION = "動畫、電影、音樂、料理與旅遊的觀後感與生活紀錄"
SITESUBTITLE = SITE_DESCRIPTION
DEFAULT_DATE_FORMAT = "%Y/%m/%d - %a"
TIMEZONE = "Asia/Taipei"
SHOW_ARTICLE_MODIFIED_TIME = True

# Page Setting
MAIN_MENU = True
DEFAULT_PAGINATION = 10
SHOW_PAGES_ON_MENU = False
SHOW_CATEGORIES_ON_MENU = False
SHOW_TAGS_IN_ARTICLE_SUMMARY = True
DIRECT_TEMPLATES = (
    "index",
    "categories",
    "archives",
    "tags",
    "series_list",
)
CATEGORIES_URL = "categories.html"
CATEGORIES_SAVE_AS = "categories.html"
ARCHIVES_URL = "archives.html"
ARCHIVES_SAVE_AS = "archives.html"
TAGS_URL = "tags.html"
TAGS_SAVE_AS = "tags.html"
SERIES_LIST_URL = "series_list.html"
SERIES_LIST_SAVE_AS = "series_list.html"

# This is a single-author site. Point author references at the about page instead
# of generating a second, paginated copy of the main article index.
AUTHOR_URL = "pages/about.html"
AUTHOR_SAVE_AS = ""

# Content Setting
ARTICLE_URL = "posts/{category}/{date:%Y}/{date:%m}/{slug}"
ARTICLE_SAVE_AS = "posts/{category}/{date:%Y}/{date:%m}/{slug}/index.html"
STATIC_PATHS = ["images", "extra", "static"]
EXTRA_PATH_METADATA = {
    "extra/robots.txt": {"path": "robots.txt"},
}

# License
CC_LICENSE = {
    "name": "創用 CC 姓名標示─相同方式分享",
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
SOCIAL_PROFILE_LABEL = "保持聯繫"
SOCIAL = (
    ("Linkedin", "https://tw.linkedin.com/in/clleew"),
    ("GitHub", "https://github.com/Lee-W"),
    ("Twitter", "https://twitter.com/clleew"),
    ("RSS", f"https://{HOST}/feeds/all.atom.xml"),
)
JINJA_GLOBALS = {"POST_SHARE_MASTODON_DOMAIN": "g0v.social"}

# Markdown extension
MARKDOWN = {
    "extension_configs": {
        "markdown.extensions.extra": {},
        "markdown.extensions.codehilite": {"css_class": "highlight"},
        "markdown.extensions.nl2br": {},
        "markdown.extensions.toc": {"toc_depth": "1-3"},
        "markdown_del_ins": {},
        "pymdownx.blocks.caption": {},
        "pymdownx.details": {},
        "pymdownx.snippets": {},
        "pymdownx.superfences": {},
        "pymdownx.tasklist": {},
    },
    "output_format": "html5",
}

# Utterance (comment system)
UTTERANCES_LABEL = "blog-comment"
COMMENTS_INTRO = '喜歡這篇文章的話，歡迎在下方留言（需要 GitHub 帳號），或是<a href="mailto:hello+travlog@wei-lee.me">寄 Email 找我聊聊！</a>'

# Theme Setting
THEME = attila.get_path()
THEME_TEMPLATES_OVERRIDES = ["theme-overrides"]
SITE_VARIANT = "travlog"
CSS_OVERRIDE = ("static/brand-travlog.css",)

# i18n
JINJA_ENVIRONMENT = {"extensions": ["jinja2.ext.i18n"]}
OG_LOCALE = "zh_TW"
DEFAULT_LANG = "zh-tw"
I18N_TEMPLATES_LANG = "en"
LANGUAGES = ()
CURRENT_LANG = "zh-tw"
I18N_SUBSITES = {}

# Plugin-setting
PLUGINS = [
    "pelican.plugins.i18n_subsites",
    "pelican.plugins.neighbors",
    "pelican.plugins.random_article",
    "pelican.plugins.render_math",
    "pelican.plugins.seo",
    "pelican.plugins.sitemap",
    "pelican.plugins.series",
    "pelican.plugins.share_post",
    "pelican.plugins.statistics",
    "pelican.plugins.summary_link",
    "pelican.plugins.tag_cloud",
    "pelican.plugins.webassets",
    "pelican.plugins.heatmap",
    "pelican.plugins.osm",
    "pelican.plugins.tabular",
    "pelican.plugins.on_this_day",
    "pelican.themes.attila.readtime",
]
PAGEFIND_ENABLED = True
RANDOM_ARTICLE_BUTTON = True
SUMMARY_LINK_FORMAT = ""
SITEMAP = {
    "format": "xml",
    "changefreqs": {
        "articles": "monthly",
        "pages": "monthly",
        "indexes": "weekly",
    },
}

# Local plugins
LOCAL_PLUGINS = [
    "image_markup",
]
PLUGIN_PATHS = ["plugins"]
PLUGINS.extend(LOCAL_PLUGINS)
# pelican-seo settings
SEO_REPORT = True  # SEO report is enabled by default
SEO_ENHANCER = False
SEO_ENHANCER_OPEN_GRAPH = False
SEO_ENHANCER_TWITTER_CARDS = False


# ----this blog only----
# Blog Conf
SITENAME = "那些沒人在乎的事"
SITETITLE = SITENAME

# Utterance (comment system)
UTTERANCES_REPO = "Lee-W/travlog"

# Page Setting
MENUITEMS = (
    ("🏠 首頁", "/"),
    ("🙋 關於", "/pages/about.html"),
    ("🗝️ 私藏", "/pages/pages.html"),
    (
        "📂 分類",
        (
            ("🍿 評論", "/category/review.html"),
            ("✈️ 旅遊", "/category/travel.html"),
            ("🥘 料理", "/category/cook.html"),
        ),
    ),
    (
        "🧭 探索",
        (
            ("🏷️ 標籤", "/tags.html"),
            ("🗄️ 歸檔", "/archives.html"),
            ("📚 系列文章", "/series_list.html"),
            ("📜 部落卷", "/pages/blogroll.html"),
        ),
    ),
    ("🎲 隨機", "/random/index.html"),
)

# Content Setting
DEFAULT_CATEGORY = "Travel"

# Theme Setting
PYGMENTS_STYLE = "default"
AUTHOR_META = {
    "Wei Lee": {
        "image": "/images/avatar.jpg",
    }
}

# Category labels
CATEGORY_TRANSLATIONS = {
    "Cook": "料理",
    "Review": "評論",
    "Travel": "旅遊",
}
