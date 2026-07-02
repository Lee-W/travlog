# travlog.wei-lee.me

Wei's entertainment blog — travel, food, and reviews. Built with [Pelican](https://getpelican.com/) and the customized [Attila](https://github.com/Lee-W/attila) theme. Deployed to Cloudflare Pages.

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

## Publishing

Drafts (`uv run inv new_draft ...`) carry `Status: draft` and are excluded from
the build. To publish one:

1. Include a commit named `new post: <title>` in the pull request.
2. Enable auto-merge.

Before the PR merges, a GitHub Actions workflow removes the draft status and
rewrites the post's `Date` to the moment it ships, so the published date is
accurate without manual editing. See
[`.github/workflows/prepare-publication.yaml`](.github/workflows/prepare-publication.yaml)
for the details.

## Deployment

Build the production output (including Pagefind), then deploy it via `wrangler`:

```bash
uv run inv preview
wrangler pages deploy output
```
