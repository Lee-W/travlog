import datetime
import glob
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from string import Template

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


def _build_pagefind():
    subprocess.run(
        ["uv", "run", "python", "-m", "pagefind", "--site", "output"],
        check=True,
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
    pelican_run("-s {settings_base}".format(**CONFIG))
    if build_pagefind:
        _build_pagefind()


@task(optional=["--build-pagefind"])
def rebuild(c, build_pagefind=False):
    """`build` with the delete switch"""
    pelican_run("-d -s {settings_base}".format(**CONFIG))
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
        "{}/templates/**/*.html".format(theme_path),
    ]

    content_file_extensions = [".md", ".rst"]
    for extension in content_file_extensions:
        content_glob = "{0}/**/*{1}".format(SETTINGS["PATH"], extension)
        watched_globs.append(content_glob)

    static_file_extensions = [".css", ".js"]
    for extension in static_file_extensions:
        static_file_glob = "{0}/static/**/*{1}".format(theme_path, extension)
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
    _build_pagefind()


def pelican_run(cmd):
    cmd += " " + program.core.remainder  # allows to pass-through args to pelican
    pelican_main(shlex.split(cmd))


@task(optional=["rev_range"])
def style(c, rev_range="origin/main.."):
    """Run style check on python code"""
    python_targets = "pelicanconf.py publishconf.py tasks.py scripts plugins tests"
    c.run(f"uv run ruff check {python_targets}")

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

    c.run(f"uv run cz check --rev-range {shlex.quote(rev_range)}")


@task
def format(c):
    """Run autoformater on python code"""
    python_targets = "pelicanconf.py publishconf.py tasks.py scripts plugins tests"
    c.run(
        f"""
        uv run ruff format {python_targets} && \
        uv run ruff check {python_targets} --fix
        """
    )


@task
def security_check(c):
    """Run pip-autid on dependencies"""
    # CVE-2026-4539 (pygments < 2.20.0) is a transitive dev-only dependency with
    # no fix available in our pinned tree; ignore until an upgrade is possible.
    c.run(
        """
        uv pip compile pyproject.toml -o requirements.txt && \
        uv run pip-audit -r requirements.txt --ignore-vuln CVE-2026-4539 && \
        rm -rf requirements.txt
        """
    )


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
    now = datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=8)))
    date_str = now.strftime("%Y-%m-%d %H:%M +0800")
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
    import hashlib
    import urllib.parse
    from collections import defaultdict

    # markdown refs may carry a Pelican {static}/{attach} prefix before /images/
    md_patterns = [
        re.compile(r"\]\(\s*(?:\{(?:static|attach)\})?(/images/[^)]+?)\s*\)"),
        re.compile(r"src=[\"'](?:\{(?:static|attach)\})?(/images/[^\"']+)[\"']"),
        re.compile(
            r"^(?:Cover|Image):\s*(?:\{(?:static|attach)\})?(/images/\S+)", re.M
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
    filenames = [
        path
        for path in glob.glob("content/images/**", recursive=True)
        if os.path.isfile(path)
    ]
    exif_tags_to_remove = ["GPSInfo"]
    for name in filenames:
        try:
            with pil_open(name) as im:
                tag_ids = _get_exif_tag_ids_by_names(exif_tags_to_remove)
                file_changed = False
                for tag_id in tag_ids:
                    if im.getexif().get(tag_id) and im._exif:
                        file_changed = True
                        im._exif[tag_id] = None

                if file_changed:
                    im.save(name)
        except FileNotFoundError, UnidentifiedImageError:
            continue
