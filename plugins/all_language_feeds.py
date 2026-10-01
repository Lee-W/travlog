"""Write Atom feeds that list the articles of every language.

FEED_ALL_LANGUAGES_ATOM is the site feed and CATEGORY_FEED_ALL_LANGUAGES_ATOM
the per-category feeds; leave both unset on the subsites so only the main
site writes them. Pelican's own FEED_ALL_ATOM only appends translations of
main-site articles, so a Japanese article without a Chinese original would be
missing; these feeds also take the articles that i18n_subsites removed from
this site because another subsite publishes them.

i18n_subsites builds the ja subsite from the main site's get_writer signal,
then points the removed articles at their subsite URL (ja/...). That happens
before the main site writes anything, so the main site's own copies of those
articles already carry the right links here; no state is shared across the
two builds. It needs I18N_UNTRANSLATED_ARTICLES = "remove" (or "keep"):
"hide" leaves the removed articles without a subsite URL.

Feeds under /zh-tw/ and /ja/ also get their own URL as <id>: Pelican uses the
site URL, so all feeds of one site would otherwise share a single id. Feeds
under /feeds/ keep Pelican's id, because subscribers already hold it.
"""

from __future__ import annotations

from collections import defaultdict
from operator import attrgetter
from urllib.parse import urlparse

from pelican import signals
from pelican.contents import Article
from pelican.utils import order_content


def all_language_articles(generator) -> list[Article]:
    """Return the published articles of every language once, in site order."""
    # Pelican's FEED_ALL_ATOM order: site articles, then their translations.
    items = list(generator.articles)
    for article in generator.articles:
        items.extend(article.translations)
    # generated_content also holds the articles i18n_subsites removed because
    # another subsite publishes them. Sort by path: files are read in no fixed
    # order, and articles with the same date keep the order they come in.
    items.extend(
        sorted(
            (
                content
                for content in generator.context["generated_content"].values()
                if isinstance(content, Article) and content.status == "published"
            ),
            key=attrgetter("source_path"),
        )
    )
    seen = set()
    articles = []
    for article in items:
        if article.source_path not in seen:
            seen.add(article.source_path)
            articles.append(article)
    return order_content(articles, order_by=generator.settings["ARTICLE_ORDER_BY"])


def _write_feeds(generator, writer) -> None:
    settings = generator.settings
    path = settings.get("FEED_ALL_LANGUAGES_ATOM")
    category_path = settings.get("CATEGORY_FEED_ALL_LANGUAGES_ATOM")
    if not path and not category_path:
        return
    articles = all_language_articles(generator)
    if path:
        writer.write_feed(
            articles,
            generator.context,
            path,
            settings.get("FEED_ALL_LANGUAGES_ATOM_URL", path),
        )
    if not category_path:
        return
    category_url = settings.get("CATEGORY_FEED_ALL_LANGUAGES_ATOM_URL", category_path)
    by_category = defaultdict(list)
    for article in articles:
        by_category[article.category].append(article)
    for category, items in by_category.items():
        writer.write_feed(
            items,
            generator.context,
            str(category_path).format(slug=category.slug),
            str(category_url).format(slug=category.slug),
            feed_title=category.name,
        )


def _use_feed_url_as_id(context, feed) -> None:
    # Assumes the site lives at the domain root: with a SITEURL path prefix
    # (https://host/blog) the old feeds would not start with "feeds/" here.
    url = feed.feed["feed_url"]
    if urlparse(url).path.lstrip("/").startswith("feeds/"):
        return
    feed.feed["id"] = url


def register() -> None:
    signals.article_writer_finalized.connect(_write_feeds)
    signals.feed_generated.connect(_use_feed_url_as_id)
