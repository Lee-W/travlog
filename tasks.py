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

from invoke.main import program
from invoke.tasks import task
from pelican import main as pelican_main
from pelican.server import ComplexHTTPRequestHandler, RootedHTTPServer
from pelican.settings import DEFAULT_CONFIG, get_settings_from_file
from PIL.ExifTags import Base as ExifBase
from PIL.Image import UnidentifiedImageError
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
    if (
        subprocess.call(["uv", "run", "python", "-m", "pagefind", "--site", "output"])
        == 1
    ):
        print("failed to call 'uv run python -m pagefind --site output'")


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


@task(optional=["--build-pagefind"])
def build_publish(c, build_pagefind=False):
    """Build pages with publishconf.py"""
    pelican_run("-s {settings_publish}".format(**CONFIG))
    if build_pagefind:
        _build_pagefind()



def pelican_run(cmd):
    cmd += " " + program.core.remainder  # allows to pass-through args to pelican
    pelican_main(shlex.split(cmd))


@task
def style(c):
    """Run style check on python code"""
    python_targets = "pelicanconf.py publishconf.py tasks.py"
    c.run(
        f"""
        uv run ruff check {python_targets} && \
        uv run cz check --rev-range origin/main..
        """
    )


@task
def format(c):
    """Run autoformater on python code"""
    python_targets = "pelicanconf.py publishconf.py tasks.py"
    c.run(
        f"""
        uv run ruff check {python_targets} --fix
        """
    )


@task
def security_check(c):
    """Run pip-autid on dependencies"""
    c.run(
        """
        uv pip compile pyproject.toml -o requirements.txt && \
        uv run pip-audit -r requirements.txt && \
        rm -rf requirements.txt
        """
    )


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

    numbers = []
    pad_width = 0
    for f in category_dir.glob("*.md"):
        m = re.match(r"^(\d+)-", f.name)
        if m:
            num_str = m.group(1)
            numbers.append(int(num_str))
            if num_str.startswith("0"):
                pad_width = len(num_str)

    n = max(numbers, default=0) + 1
    n_str = str(n).zfill(pad_width) if pad_width else str(n)

    template = Template((Path("templates") / template_name).read_text())
    content = template.substitute(
        title=title, date=date_str, category=category, slug=slug, **(extra or {})
    )

    filepath = category_dir / f"{n_str}-{slug}.md"
    filepath.write_text(content)
    print(f"Created: {filepath}")


@task
def new_post(c, title, category, slug="", lang="zh-tw"):
    """Create a new post file from template"""
    _create_post_from_template("post.md", title, category, slug, {"lang": lang})


@task
def new_seasonal_review(c, year, season):
    """Create a new 本季看什麼 post (--year YYYY --season winter/spring/summer/fall)"""
    season_zh = _SEASONS[season.lower()]
    title = f"{year} {season_zh}看什麼"
    slug = f"what-i-watched-in-{year}-{season.lower()}"
    _create_post_from_template("seasonal-review.md", title, "Review", slug)


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
        except (FileNotFoundError, UnidentifiedImageError):
            continue
