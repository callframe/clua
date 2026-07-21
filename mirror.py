#!/usr/bin/env python3
"""Mirror the Lua reference manual of a given version into the current directory."""

import argparse
import re
import shutil
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urldefrag, urljoin, unquote
from urllib.request import Request, urlopen

BASE = "https://www.lua.org/manual/"
ENTRY = "index.html"
ENCODING = "iso-8859-1"
HTML_TYPES = {"text/html", "application/xhtml+xml"}

PARSER = argparse.ArgumentParser(
    description="Mirror the Lua reference manual of a given version into the current directory."
)
PARSER.add_argument("lua_version", help="Lua manual version, for example 5.5")
PARSER.add_argument(
    "output_dir",
    nargs="?",
    default=None,
    help="Output directory for the mirrored manual (default: spec)",
)


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        self.urls += [v for k, v in attrs if k in ("href", "src") and v]


def fetch(url):
    with urlopen(Request(url, headers={"User-Agent": "mirror.py"})) as response:
        return response.read(), response.headers.get_content_type()


def relative_to(url, base):
    if not url.startswith(base):
        return None
    path = unquote(url[len(base) :]) or ENTRY
    if path.endswith("/"):
        path += ENTRY
    if path.startswith("/") or ".." in path.split("/"):
        return None
    return Path(path)


def links(page, url, base):
    parser = LinkParser()
    parser.feed(page.decode(ENCODING))
    for reference in parser.urls:
        target, _ = urldefrag(urljoin(url, reference))
        if relative_to(target, base):
            yield target


def download(base, out_dir):
    seen = {base}
    queue = [base]
    while queue:
        url = queue.pop(0)
        try:
            page, content_type = fetch(url)
        except URLError as error:
            print(f"    skipped {url}: {error}")
            continue

        path = out_dir / relative_to(url, base)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(page)
        print(f"    {path.relative_to(out_dir)}")

        if content_type in HTML_TYPES:
            for target in links(page, url, base):
                if target not in seen:
                    seen.add(target)
                    queue.append(target)


def patch_links(path, base, version):
    text = path.read_text(encoding=ENCODING)
    patched = re.sub(rf"{re.escape(base)}(?=[\w.#])", "", text, flags=re.I)
    patched = re.sub(
        rf"(?<=[\"'/]){re.escape(version)}\.html", ENTRY, patched, flags=re.I
    )
    if patched != text:
        path.write_text(patched, encoding=ENCODING)


def move_into(src_dir, out_dir):
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    for entry in src_dir.iterdir():
        shutil.move(entry, out_dir / entry.name)


def main():
    args = PARSER.parse_args()

    version = args.lua_version
    base = f"{BASE}{version}/"
    if args.output_dir is None:
        out_dir = (Path(__file__).resolve().parent / "spec").resolve()
    else:
        out_dir = Path(args.output_dir).resolve()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        print(f"==> Downloading Lua {version} manual...")
        download(base, tmp_dir)
        if not any(tmp_dir.iterdir()):
            raise SystemExit(f"Failed to download the manual from {base}")

        print("==> Moving files...")
        move_into(tmp_dir, out_dir)

    contents = out_dir / f"{version}.html"
    if contents.exists():
        print(f"==> Renaming {version}.html -> {ENTRY}...")
        contents.replace(out_dir / ENTRY)

    print("==> Patching links...")
    for path in out_dir.glob("*.html"):
        patch_links(path, base, version)


if __name__ == "__main__":
    main()
