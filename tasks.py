import datetime
import glob
import hashlib
import os
import posixpath
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from string import Template
from urllib.parse import unquote, urlparse
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from invoke.exceptions import Exit
from invoke.main import program
from invoke.tasks import task
from pelican import main as pelican_main
from pelican.server import ComplexHTTPRequestHandler, RootedHTTPServer
from pelican.settings import DEFAULT_CONFIG, get_settings_from_file
from PIL.ExifTags import Base as ExifBase
from PIL.Image import Resampling, UnidentifiedImageError
from PIL.Image import open as pil_open

OPEN_BROWSER_ON_SERVE = True
SETTINGS_FILE_BASE = "pelicanconf.py"
SETTINGS = {}
SETTINGS.update(DEFAULT_CONFIG)
LOCAL_SETTINGS = get_settings_from_file(SETTINGS_FILE_BASE)
SETTINGS.update(LOCAL_SETTINGS)

CONFIG = {
    "settings_base": SETTINGS_FILE_BASE,
    "settings_publish": "publishconf.py",
    # Output path. Can be absolute or relative to tasks.py. Default: 'output'
    "deploy_path": SETTINGS["OUTPUT_PATH"],
    # Host and port for `serve`
    "host": "localhost",
    "port": 8000,
}


def _base_cmd(build_pagefind):
    """pelican args for the dev config.

    The theme renders the search button whenever PAGEFIND_ENABLED is true, but
    the button only works once `pagefind` has built the index. Without
    --build-pagefind the index is absent, so turn the button off instead of
    shipping one that silently does nothing.
    """
    cmd = "-s {settings_base}"
    if not build_pagefind:
        cmd += " -e PAGEFIND_ENABLED=false"
    return cmd


def _build_pagefind():
    subprocess.run(
        ["uv", "run", "--no-sync", "python", "-m", "pagefind", "--site", "output"],
        check=True,
    )


def _find_output_target(output_root: Path, page: Path, href: str) -> Path | None:
    """Return the generated file `href` resolves to, or None if it is missing."""
    parsed = urlparse(href)
    if parsed.netloc and parsed.netloc not in {
        SETTINGS["HOST"],
        urlparse(SETTINGS["SITEURL"]).netloc,
    }:
        return None
    if parsed.scheme in {"mailto", "tel", "javascript"} or not parsed.path:
        return None

    if parsed.path.startswith("/"):
        target = output_root / unquote(parsed.path.lstrip("/"))
    else:
        target = page.parent / unquote(parsed.path)
    # Articles are published as <slug>/index.html under an extensionless URL.
    candidates = [target / "index.html"] if target.is_dir() else [target]
    if not target.suffix:
        candidates.extend((target / "index.html", target.with_suffix(".html")))
    return next(
        (candidate.resolve() for candidate in candidates if candidate.is_file()), None
    )


def _add_hreflang_links(soup: BeautifulSoup) -> bool:
    """Add alternate-language metadata for pages with real translations."""
    canonical = soup.select_one('link[rel="canonical"][href]')
    language_menu = soup.select_one("#nav-language-menu")
    if canonical is None or language_menu is None or soup.head is None:
        return False

    canonical_url = canonical["href"]
    canonical_path = urlparse(canonical_url).path
    site_root = urllib.parse.urljoin(canonical_url, "/")
    language_roots = {
        urlparse(root).path.rstrip("/"): "zh-TW" if lang == "zh-tw" else lang
        for lang, root in SETTINGS["LANGUAGES"]
    }
    alternates: dict[str, str] = {}
    for anchor in language_menu.find_all("a", href=True):
        path = urlparse(anchor["href"]).path
        # The language picker falls back to a subsite's home page when no
        # translation exists. Do not advertise that fallback as a translation.
        if (
            path.rstrip("/") in language_roots
            and canonical_path.rstrip("/") not in language_roots
        ):
            continue
        for root in sorted(language_roots, key=len, reverse=True):
            if path.rstrip("/") == root or path.startswith(f"{root}/"):
                alternates[language_roots[root]] = urllib.parse.urljoin(site_root, path)
                break

    if len(alternates) < 2:
        return False

    for old_link in soup.select('link[rel="alternate"][hreflang]'):
        old_link.decompose()
    for lang, href in sorted(alternates.items()):
        soup.head.append(
            soup.new_tag("link", rel="alternate", hreflang=lang, href=href)
        )
    if "zh-TW" in alternates:
        soup.head.append(
            soup.new_tag(
                "link",
                rel="alternate",
                hreflang="x-default",
                href=alternates["zh-TW"],
            )
        )
    return True


def _normalize_sitemap(path: Path) -> int:
    """Merge duplicate sitemap entries (untranslated pages appear in both sites)."""
    if not path.exists():
        return 0

    sitemap_namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"
    xhtml_namespace = "http://www.w3.org/1999/xhtml"
    ET.register_namespace("", sitemap_namespace)
    ET.register_namespace("xhtml", xhtml_namespace)
    tree = ET.parse(path)
    root = tree.getroot()
    loc_tag = f"{{{sitemap_namespace}}}loc"
    alternate_tag = f"{{{xhtml_namespace}}}link"
    seen: dict[str, ET.Element] = {}
    duplicates = 0

    for url_element in list(root):
        loc = url_element.find(loc_tag)
        if loc is None or not loc.text:
            continue
        if loc.text in seen:
            target = seen[loc.text]
            existing_languages = {
                link.get("hreflang") for link in target.findall(alternate_tag)
            }
            for alternate in url_element.findall(alternate_tag):
                if alternate.get("hreflang") not in existing_languages:
                    target.append(alternate)
            root.remove(url_element)
            duplicates += 1
            continue
        seen[loc.text] = url_element

    tree.write(path, encoding="utf-8", xml_declaration=True)
    return duplicates


def _fix_internal_links() -> None:
    """Repair generated links for i18n, add hreflang and dedupe the sitemap."""
    output_root = Path(CONFIG["deploy_path"]).resolve()
    # Longest first, so /ja/ never loses to the default language's "/".
    subsite_roots = sorted(
        (
            urlparse(language_root).path
            for _, language_root in SETTINGS["LANGUAGES"]
            if urlparse(language_root).path.strip("/")
        ),
        key=len,
        reverse=True,
    )

    fixed = 0
    hreflang_pages = 0
    for page in output_root.rglob("*.html"):
        soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
        changed = False
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            parsed = urlparse(href)
            if (
                parsed.netloc
                and parsed.netloc
                not in {SETTINGS["HOST"], urlparse(SETTINGS["SITEURL"]).netloc}
                or parsed.scheme in {"mailto", "tel", "javascript"}
                or not parsed.path
                or _find_output_target(output_root, page, href) is not None
            ):
                continue
            # The language picker links to a translation that was never built
            # (articles are not generated in /ja/); it carries its own fallback.
            replacement = anchor.get("data-fallback")
            if replacement is None and "/../" in parsed.path:
                replacement = posixpath.normpath(parsed.path)
            if replacement is None and (
                "/tag/" in parsed.path
                or "/category/" in parsed.path
                or "/author/" in parsed.path
            ):
                # Fall back to the home page of the subsite the link sits in.
                replacement = next(
                    (root for root in subsite_roots if parsed.path.startswith(root)),
                    "/",
                )
            if replacement is None:
                continue
            anchor["href"] = parsed._replace(path=replacement).geturl()
            changed = True
            fixed += 1
        if _add_hreflang_links(soup):
            changed = True
            hreflang_pages += 1
        if changed:
            page.write_text(str(soup), encoding="utf-8")
    sitemap_duplicates = _normalize_sitemap(output_root / "sitemap.xml")
    print(
        f"Fixed {fixed} generated internal link(s); "
        f"added hreflang to {hreflang_pages} page(s); "
        f"removed {sitemap_duplicates} duplicate sitemap URL(s)"
    )


@task
def clean(c):
    """Remove generated files"""
    if os.path.isdir(CONFIG["deploy_path"]):
        shutil.rmtree(CONFIG["deploy_path"])
        os.makedirs(CONFIG["deploy_path"])


@task(optional=["--build-pagefind"])
def build(c, build_pagefind=False):
    """Build local version of site"""
    pelican_run(_base_cmd(build_pagefind).format(**CONFIG))
    _fix_internal_links()
    if build_pagefind:
        _build_pagefind()


@task(optional=["--build-pagefind"])
def rebuild(c, build_pagefind=False):
    """`build` with the delete switch"""
    pelican_run(("-d " + _base_cmd(build_pagefind)).format(**CONFIG))
    _fix_internal_links()
    if build_pagefind:
        _build_pagefind()


@task
def regenerate(c):
    """Automatically regenerate site upon file modification"""
    pelican_run("-r -s {settings_base}".format(**CONFIG))


@task
def serve(c):
    """Serve site at http://$HOST:$PORT/ (default is localhost:8000)"""

    class AddressReuseTCPServer(RootedHTTPServer):
        allow_reuse_address = True

    server = AddressReuseTCPServer(
        CONFIG["deploy_path"],
        (CONFIG["host"], CONFIG["port"]),
        ComplexHTTPRequestHandler,
    )

    if OPEN_BROWSER_ON_SERVE:
        # Open site in default browser
        import webbrowser

        webbrowser.open("http://{host}:{port}".format(**CONFIG))

    sys.stderr.write("Serving at {host}:{port} ...\n".format(**CONFIG))
    server.serve_forever()


@task
def reserve(c):
    """`build`, then `serve`"""
    build(c, build_pagefind=False)
    serve(c)


@task
def preview(c):
    """Build production version of site"""
    pelican_run("-s {settings_publish}".format(**CONFIG))
    _fix_internal_links()
    _build_pagefind()


@task
def livereload(c):
    """Automatically reload browser tab upon file modification."""
    from livereload import Server

    def cached_build():
        cmd = "-s {settings_base} -e CACHE_CONTENT=true LOAD_CONTENT_CACHE=true"
        pelican_run(cmd.format(**CONFIG))

    cached_build()
    server = Server()
    theme_path = SETTINGS["THEME"]
    watched_globs = [
        CONFIG["settings_base"],
        f"{theme_path}/templates/**/*.html",
    ]

    content_file_extensions = [".md", ".rst"]
    for extension in content_file_extensions:
        content_glob = f"{SETTINGS['PATH']}/**/*{extension}"
        watched_globs.append(content_glob)

    static_file_extensions = [".css", ".js"]
    for extension in static_file_extensions:
        static_file_glob = f"{theme_path}/static/**/*{extension}"
        watched_globs.append(static_file_glob)

    for g in watched_globs:
        server.watch(g, cached_build)

    if OPEN_BROWSER_ON_SERVE:
        # Open site in default browser
        import webbrowser

        webbrowser.open("http://{host}:{port}".format(**CONFIG))

    server.serve(host=CONFIG["host"], port=CONFIG["port"], root=CONFIG["deploy_path"])


@task
def build_publish(c):
    """Build pages with publishconf.py"""
    pelican_run("-s {settings_publish}".format(**CONFIG))
    _fix_internal_links()
    _build_pagefind()


def _build_tabular_data():
    """Generate the catalog before localizing all tabular data."""
    subprocess.run([sys.executable, "scripts/build_story_database.py"], check=True)
    subprocess.run([sys.executable, "scripts/build_ja_data.py"], check=True)


def pelican_run(cmd):
    _build_tabular_data()
    cmd += " " + program.core.remainder  # allows to pass-through args to pelican
    pelican_main(shlex.split(cmd))


@task(optional=["rev_range"])
def style(c, rev_range="origin/main.."):
    """Run style check on python code"""
    python_targets = "pelicanconf.py publishconf.py tasks.py scripts plugins tests"
    c.run(f"uv run --no-sync ruff check {python_targets}")

    commit_count = subprocess.run(
        ["git", "rev-list", "--count", rev_range],
        check=False,
        capture_output=True,
        text=True,
    )
    if commit_count.returncode != 0:
        print(f"Skipping commit style check: invalid rev range {rev_range!r}")
        return

    if commit_count.stdout.strip() == "0":
        print(f"Skipping commit style check: no commits in {rev_range!r}")
        return

    c.run(f"uv run --no-sync cz check --rev-range {shlex.quote(rev_range)}")


@task
def format(c):
    """Run autoformater on python code"""
    python_targets = "pelicanconf.py publishconf.py tasks.py scripts plugins tests"
    c.run(
        f"""
        uv run --no-sync ruff format {python_targets} && \
        uv run --no-sync ruff check {python_targets} --fix
        """
    )


@task
def security_check(c):
    """Run pip-audit on the dependency versions pinned in uv.lock"""
    # pelican 4.12.0 pins pygments<2.20.0; the fix (2.20.0) cannot be installed yet
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False
    ) as requirements_file:
        requirements_path = requirements_file.name

    try:
        c.run(
            "uv export --frozen --no-hashes --format requirements-txt "
            f"-o {shlex.quote(requirements_path)}"
        )
        c.run(
            f"uv run --no-sync pip-audit -r {shlex.quote(requirements_path)} "
            "--disable-pip --no-deps --ignore-vuln CVE-2026-4539"
        )
    finally:
        Path(requirements_path).unlink(missing_ok=True)


@task
def check_content(c):
    """Run local content quality checks."""
    post_files = sorted(str(path) for path in Path("content/posts").rglob("*.md"))
    metadata_check = subprocess.run(
        [
            sys.executable,
            "scripts/check_post_metadata.py",
            "--categories",
            "Review,Cook,Travel",
            *post_files,
        ],
        check=False,
    )
    if metadata_check.returncode != 0:
        raise Exit(metadata_check.returncode)

    page_files = sorted(str(path) for path in Path("content/pages").glob("*.md"))
    page_metadata_check = subprocess.run(
        [sys.executable, "scripts/check_page_metadata.py", *page_files],
        check=False,
    )
    if page_metadata_check.returncode != 0:
        raise Exit(page_metadata_check.returncode)

    check_image_usage(c)


_SEASONS = {
    "winter": "冬季",
    "spring": "春季",
    "summer": "夏季",
    "fall": "秋季",
}


def _create_post_from_template(
    template_name: str,
    title: str,
    category: str,
    slug: str = "",
    extra: dict | None = None,
) -> None:
    now = datetime.datetime.now(tz=ZoneInfo("Asia/Tokyo"))
    date_str = now.strftime("%Y-%m-%d %H:%M %z")
    year = now.strftime("%Y")

    if not slug:
        slug = re.sub(r"[^\w\s-]", "", title.lower())
        slug = re.sub(r"[\s_]+", "-", slug).strip("-") or title

    category_dir = Path("content/posts") / category.lower().replace(" ", "-") / year
    category_dir.mkdir(parents=True, exist_ok=True)

    template = Template((Path("templates") / template_name).read_text())
    content = template.substitute(
        title=title, date=date_str, category=category, slug=slug, **(extra or {})
    )

    filepath = category_dir / f"{slug}.md"
    filepath.write_text(content)
    print(f"Created: {filepath}")


@task
def new_post(c, title, category, slug="", lang="zh-tw"):
    """Create a new post file from template"""
    _create_post_from_template("post.md", title, category, slug, {"lang": lang})


@task
def new_draft(c, title, category, slug="", lang="zh-tw"):
    """Create a new draft file from template"""
    _create_post_from_template("draft.md", title, category, slug, {"lang": lang})


@task
def new_seasonal_review(c, year, season):
    """Create a new 本季看什麼 post (--year YYYY --season winter/spring/summer/fall)"""
    season_zh = _SEASONS[season.lower()]
    title = f"{year} {season_zh}看什麼"
    slug = f"what-i-watched-in-{year}-{season.lower()}"
    _create_post_from_template("seasonal-review.md", title, "Review", slug)


def _dhash(path: Path, hash_size: int = 8) -> int | None:
    """Perceptual difference-hash of an image (None if it can't be opened)."""
    try:
        with pil_open(path) as im:
            small = im.convert("L").resize(
                (hash_size + 1, hash_size), Resampling.LANCZOS
            )
    except UnidentifiedImageError, OSError, ValueError:
        return None
    pixels = list(small.getdata())
    bits = 0
    for row in range(hash_size):
        for col in range(hash_size):
            left = pixels[row * (hash_size + 1) + col]
            right = pixels[row * (hash_size + 1) + col + 1]
            bits = (bits << 1) | int(left > right)
    return bits


@task
def check_image_usage(_) -> None:
    """Report orphan, cross-article reused, and duplicate-content images."""

    # markdown refs may carry a Pelican {static}/{attach} prefix before /images/
    md_patterns = [
        re.compile(r"\]\(\s*(?:\{(?:static|attach)\})?(/images/[^)]+?)\s*\)"),
        re.compile(r"src=[\"'](?:\{(?:static|attach)\})?(/images/[^\"']+)[\"']"),
        re.compile(
            r"^(?:Cover|Image):\s*(?:\{(?:static|attach)\})?(/images/\S+)", re.MULTILINE
        ),
    ]
    # content/places/*.yaml reference images directly as list items / keys
    yaml_pattern = re.compile(r"/images/[^\s\"']+")
    refs: dict[str, set[str]] = defaultdict(set)
    for path in Path("content").rglob("*"):
        if path.suffix == ".md" and ("posts" in path.parts or "pages" in path.parts):
            text = path.read_text()
            for pattern in md_patterns:
                for match in pattern.findall(text):
                    refs[urllib.parse.unquote(match.strip())].add(str(path))
        elif path.suffix in {".yaml", ".yml"}:
            text = path.read_text()
            for match in yaml_pattern.findall(text):
                refs[urllib.parse.unquote(match.strip())].add(str(path))

    config_used = {"/images/avatar.jpg", "/images/cover.jpeg"}
    disk = {
        f"/{path.relative_to('content')}": path
        for path in Path("content/images").rglob("*")
        if path.is_file() and path.name != ".DS_Store"
    }

    orphans = sorted(
        (path.stat().st_size, url)
        for url, path in disk.items()
        if url not in refs and url not in config_used
    )
    print(f"=== Orphan images: {len(orphans)} ===")
    for size, url in reversed(orphans):
        print(f"  {size / 1024 / 1024:6.2f} MB  {url}")

    reused = {
        url: files
        for url, files in refs.items()
        if len(files) > 1 and url in disk and "/meme/" not in url
    }
    print(f"\n=== Reused across articles (outside /images/meme/): {len(reused)} ===")
    print("    (referencing the original post folder is fine;")
    print("     consider moving to /images/meme/ only if it is a meme)")
    for url, files in sorted(reused.items()):
        print(f"  {url}")
        for f in sorted(files):
            print(f"      {f}")

    by_digest: dict[str, list[str]] = defaultdict(list)
    digest_by_url: dict[str, str] = {}
    for url, path in disk.items():
        digest = hashlib.md5(path.read_bytes()).hexdigest()
        by_digest[digest].append(url)
        digest_by_url[url] = digest
    duplicates = [sorted(urls) for urls in by_digest.values() if len(urls) > 1]
    print(f"\n=== Identical file contents: {len(duplicates)} group(s) ===")
    for urls in sorted(duplicates):
        print("  " + " == ".join(urls))

    # Near-duplicates: visually similar but not byte-identical (re-compressed,
    # resized, or EXIF-stripped copies that md5 alone cannot catch).
    near_dup_threshold = 5
    hashes = [(url, h) for url in disk if (h := _dhash(disk[url])) is not None]
    near_dups = []
    for i, (url_a, hash_a) in enumerate(hashes):
        for url_b, hash_b in hashes[i + 1 :]:
            if digest_by_url[url_a] == digest_by_url[url_b]:
                continue  # already reported above as identical contents
            distance = (hash_a ^ hash_b).bit_count()
            if distance <= near_dup_threshold:
                near_dups.append((distance, url_a, url_b))
    near_dups.sort()
    print(
        f"\n=== Near-duplicate images "
        f"(perceptual, Hamming <= {near_dup_threshold}): {len(near_dups)} pair(s) ==="
    )
    for distance, url_a, url_b in near_dups:
        print(f"  d={distance}  {url_a}  ~~  {url_b}")

    dead = sorted(url for url in refs if url not in disk)
    print(f"\n=== Referenced but missing on disk: {len(dead)} ===")
    for url in dead:
        print(f"  {url}")
        for f in sorted(refs[url]):
            print(f"      {f}")


def _get_exif_tag_ids_by_names(names: Sequence[str]) -> set[int]:
    return {getattr(ExifBase, name).value for name in names}


@task
def check_and_remove_image_exif_gps_info(_) -> None:
    """Check and remove GPSInfo from image EXIF if exists."""
    # Pilgrimage photos intentionally keep their GPS EXIF (that's the whole
    # point of a pilgrimage record), so they're excluded here directly rather
    # than relying on the pre-commit hook's `exclude:` filter -- that filter
    # only decides whether the hook *runs* (moot once pass_filenames: false
    # means every invocation still glob-scans the whole tree below).
    excluded_dir = os.path.join("content", "images", "pilgrimage") + os.sep
    filenames = [
        path
        for path in glob.glob("content/images/**", recursive=True)
        if os.path.isfile(path) and not path.startswith(excluded_dir)
    ]
    exif_tags_to_remove = ["GPSInfo"]
    for name in filenames:
        try:
            with pil_open(name) as im:
                exif = im.getexif()
                tag_ids = _get_exif_tag_ids_by_names(exif_tags_to_remove)
                file_changed = False
                for tag_id in tag_ids:
                    if tag_id in exif:
                        file_changed = True
                        del exif[tag_id]

                if file_changed:
                    im.save(name, exif=exif)
        except FileNotFoundError, UnidentifiedImageError:
            continue
