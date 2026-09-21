"""Keep a random-article entry point for subsites without published articles."""

from pathlib import Path

from pelican import signals
from pelican.plugins.random_article.random_article import generate_random_page


def _generate_random_page(generator):
    fallback_url = generator.settings.get("RANDOM_ARTICLE_FALLBACK_URL")
    if generator.articles or not fallback_url:
        generate_random_page(generator)
        return

    # The main site's random page applies the upstream exclusion rules. Once
    # this subsite has articles, the branch above uses its own pool instead.
    template = generator.get_template("random-article-fallback")
    output = Path(generator.output_path) / generator.settings.get(
        "RANDOM_ARTICLE_SAVE_AS", "random/index.html"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        template.render(generator.context, fallback_url=fallback_url),
        encoding="utf-8",
    )


def register():
    signals.article_generator_finalized.connect(_generate_random_page)
