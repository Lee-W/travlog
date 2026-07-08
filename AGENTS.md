# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Overview

This is a personal entertainment blog built with [Pelican](https://getpelican.com/) (Python static site generator), using a customized [Attila](https://github.com/Lee-W/attila) theme. Content is written in Markdown. The site is deployed to Cloudflare Pages via `wrangler.toml`.

## Common Commands

All tasks are run via `invoke` (using `uv run`):

```bash
uv run inv build           # Build local version of site
uv run inv rebuild         # Build with delete switch (clean build)
uv run inv serve           # Serve site at localhost:8000
uv run inv reserve         # Build then serve
uv run inv livereload      # Build and serve with live reload on file changes
uv run inv clean           # Remove generated files in output/
uv run inv preview         # Build production version (uses publishconf.py)
uv run inv build_publish   # Build production version with publishconf.py (alias for preview)
uv run inv style           # Run ruff linting + commitizen commit style check
uv run inv format          # Auto-fix ruff format + lint issues
uv run inv security_check  # Run pip-audit on dependencies
uv run inv check_and_remove_image_exif_gps_info  # Strip GPS EXIF from images
```

Build with pagefind search index:

```bash
uv run inv build --build-pagefind
```

Create new content:

```bash
uv run inv new_post --title "Title" --category "Review"          # New post
uv run inv new_draft --title "Title" --category "Travel"         # New draft (Status: draft)
uv run inv new_seasonal_review --year 2026 --season spring       # New 本季看什麼 post
```

## Architecture

### Configuration

- `pelicanconf.py` — development config (SITEURL is `localhost:8000`, feeds disabled)
- `publishconf.py` — production config (extends pelicanconf, enables feeds, reads `UMAMI_WEBSITE_ID` env var)
- `tasks.py` — all invoke task definitions

### Content Structure

```text
content/
  posts/
    review/    # Anime, film, book reviews (本季看什麼 etc.)
    travel/    # Travel posts
    cook/      # Cooking posts
  pages/       # Static pages (about, etc.)
  images/      # Post images
  static/      # Static files excluded from article processing
  extra/       # Extra files like CNAME
  places/      # OSM/map data (pilgrimage, theaters, etc.)
  data/        # YAML data files (story-ranking, concerts, etc.)
```

Posts are organized by category then year (e.g., `content/posts/review/2026/`). Filenames are prefixed with a sequential number (e.g., `14-what-i-watched-in-2026-spring.md`).

### Post Metadata

Each post uses Pelican metadata headers:

```markdown
Title: Post Title
Date: 2026-01-01 12:00 +0800
Category: Review
Tags: tag1, tag2
Slug: post-slug
Cover: /images/posts-image/...  # optional
Authors: Wei Lee
Lang: zh-tw                     # optional, defaults to zh-tw
Series: Series Name             # optional
```

The `<!--more-->` marker defines the article summary cutoff.

### Plugins

Key plugins configured in `pelicanconf.py`:
- `pelican.plugins.i18n_subsites` — bilingual site support (zh-tw default, en subsite)
- `pelican.plugins.series` — groups posts into series
- `pelican.plugins.webassets` — CSS/JS asset bundling
- `pelican.plugins.seo` — SEO report and enhancer
- `pelican.plugins.deadlinks` — dead link validation (disabled by default)
- `pelican.plugins.tabular` — table rendering from YAML data files
- `pelican.plugins.osm` — OpenStreetMap integration for pilgrimage/place data
- `pagefind` — client-side search (must be built separately with `--build-pagefind`)

### Commit Convention

Uses commitizen with custom types. Valid commit prefixes:
`new post`, `post update`, `new draft`, `draft update`, `post metadata`, `typo`, `config`, `theme`, `dependency`, `static page`

Format: `<type>: <message>`

Run `uv run cz commit` for interactive commit, or `uv run cz check` to validate.
