# travlog.wei-lee.me

Wei's entertainment blog — travel, food, and reviews. Built with [Pelican](https://getpelican.com/) and the customized [Attila](https://github.com/Lee-W/attila) theme. Deployed to Cloudflare Workers (static assets).

## Commands

```bash
uv run inv build           # Build local version of site
uv run inv rebuild         # Clean build
uv run inv serve           # Serve at localhost:8000
uv run inv reserve         # Build then serve
uv run inv livereload      # Build and serve with live reload
uv run inv clean           # Remove generated files
uv run inv preview         # Build production version, including Pagefind
uv run inv style           # Lint + commit style check
uv run inv format          # Auto-fix lint issues
uv run inv check-content   # Check post metadata and image usage
uv run inv security_check  # Audit dependencies
uv run inv check_and_remove_image_exif_gps_info  # Strip GPS EXIF from images
uv run inv check-image-usage  # Report orphan, reused, duplicate, and missing images
```

Build with search index:

```bash
uv run inv build --build-pagefind
```

## Content Structure

```text
content/
  posts/
    cook/      # Cooking posts
    review/    # Reviews
    travel/    # Travel posts
  pages/       # Static pages
  images/      # Post images
  places/      # OSM/map data
  static/      # Static files excluded from article processing
  extra/       # Extra static files
```

## Works database

The ranking page at `/pages/story-ranking.html` uses the searchable catalog,
with a Japanese version at `/ja/pages/story-ranking.html`. Its original ranking
explanation is preserved in a collapsible section. The view and its compact
layout are opted into by these two pages; other tables keep their existing UI.

Keep editing the nine YAML files under `content/data/story-ranking/`.
Every `inv` task that runs Pelican (`build`, `rebuild`, `regenerate`, `preview`,
`build_publish`, `livereload`, `reserve`) first generates the ignored
`content/data/story-database.yaml`. Japanese titles live in each source record's
`translations.ja.title`; the generated catalog preserves the translation mapping
and Tabular selects the title for the page language. `build_ja_data.py` copies
the catalog unchanged and retains compatibility handling for other tables and
place data.
Do not edit or commit that generated file. Adding a category requires adding
its labels to `scripts/build_story_database.py`; an unknown category fails the
build so no entries silently disappear.

The catalog preserves separate seasons/entries, tiers and review links. It
supports searching both Taiwanese Mandarin and native titles, filtering by
category/Tier/review availability, numerical preference sorting, URL state and
compact mobile rows. It does not infer viewing progress or publication dates from
ranking categories or review dates. Star Wars novels retain their separate
ranking page. The catalog keeps Star Wars as the author's separate category,
without exposing its source-specific grouping field on unrelated works.
`check_story_ranking.py` checks source coverage through the catalog builder's
category list as well as direct table references.

`theme-overrides/story-ranking.html` opts into the page layout and loads
`content/static/story-database.css` for page notes, column proportions and
category/Tier styling. Tabular supplies the shared controls, typography and
responsive labels. It opens filters by default above 680px, collapses them on
smaller screens, and preserves manual toggles for the current page. Each row
displays the page's localized work name; alternate titles remain searchable.

## Publishing

Drafts (`uv run inv new_draft ...`) and new posts (`uv run inv new_post ...`)
are created without numeric prefixes. Drafts carry `Status: draft` and are
excluded from the build. To publish one:

1. Include a commit named `new post: <title>` in the pull request.
2. Enable auto-merge.

Before the PR merges, a GitHub Actions workflow assigns the final sequence
number, removes the draft status, and rewrites the post's `Date` to the
moment it ships. References using Pelican's `{filename}/posts/...` syntax are
updated with the final filename and checked for missing targets, so the
published date and internal links stay accurate without manual editing. See
[`.github/workflows/prepare-publication.yaml`](.github/workflows/prepare-publication.yaml)
for the details.

## Deployment

Build the production output (including Pagefind), then deploy it via `wrangler`
(project config lives in `wrangler.toml`, which points `[assets]` at `output`):

```bash
uv run inv preview
wrangler deploy
```
