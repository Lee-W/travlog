# -*- coding: utf-8 -*-

import datetime
import glob
import os
import shlex
import shutil
import subprocess
import sys
from collections.abc import Sequence

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
    # Github Pages configuration
    "github_pages_branch": "gh-pages",
    "commit_message": "'Publish site on {}'".format(datetime.date.today().isoformat()),
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


@task
def gh_pages(c):
    """Publish to GitHub Pages"""
    preview(c)
    c.run(
        "ghp-import -b {github_pages_branch} "
        "-m {commit_message} "
        "{deploy_path} -p".format(**CONFIG)
    )


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
