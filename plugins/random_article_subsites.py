"""Keep a random-article entry point for subsites without published articles."""

import json
from pathlib import Path

from markupsafe import Markup
from pelican import signals
from pelican.plugins.random_article.random_article import _is_excluded


def _article_urls(generator):
    """Published article URLs after the upstream exclusion rules."""
    context = generator.context
    exclude_categories = context.get("RANDOM_ARTICLE_EXCLUDE_CATEGORIES", []) or []
    exclude_tags = context.get("RANDOM_ARTICLE_EXCLUDE_TAGS", []) or []
    siteurl = context.get("SITEURL", "")
    urls = []
    for article in generator.articles:
        if getattr(article, "status", "published") != "published":
            continue
        if _is_excluded(article, exclude_categories, exclude_tags):
            continue
        url = article.url
        if siteurl and not url.startswith(("http://", "https://")):
            url = siteurl.rstrip("/") + "/" + url.lstrip("/")
        urls.append(url)
    return urls


def _generate_random_page(generator):
    fallback_url = generator.settings.get("RANDOM_ARTICLE_FALLBACK_URL")
    urls = _article_urls(generator)
    # The main site's random page applies the upstream exclusion rules. A
    # subsite with no eligible articles redirects to the fallback instead.
    if urls or not fallback_url:
        # Own template (not upstream's built-in one) so the page carries
        # lang, viewport, description, canonical and an h1.
        template = generator.get_template("random-article")
        # Pre-serialised JSON is safe inside <script>; mark it so it is not escaped.
        html = template.render(
            generator.context, article_urls_json=Markup(json.dumps(urls))
        )
    else:
        template = generator.get_template("random-article-fallback")
        html = template.render(generator.context, fallback_url=fallback_url)
    output = Path(generator.output_path) / generator.settings.get(
        "RANDOM_ARTICLE_SAVE_AS", "random/index.html"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")


def register():
    signals.article_generator_finalized.connect(_generate_random_page)
