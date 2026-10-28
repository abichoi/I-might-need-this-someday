"""Append a link submitted through a GitHub issue to links.yml.

The issue body must contain a ```yaml block holding either one mapping
or a one-item list with at least a `url`. Reads the body from the
ISSUE_BODY environment variable. Prints the saved title on success.
"""
import datetime
import html
import os
import re
import sys
import urllib.request

import yaml

LINKS_FILE = os.environ.get("LINKS_FILE", "links.yml")
FIELD_ORDER = ["url", "title", "note", "tags", "added", "found_via"]


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def fetch_title(url):
    """Best-effort: read the <title> of the page so blank titles get filled in."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (link-collector)"})
        with urllib.request.urlopen(req, timeout=10) as r:
            text = r.read(300_000).decode("utf-8", "ignore")
        m = re.search(r"<title[^>]*>(.*?)</title>", text, re.S | re.I)
        if m:
            return html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()[:200] or None
    except Exception:
        pass
    return None


def main():
    body = os.environ.get("ISSUE_BODY", "")
    m = re.search(r"```ya?ml\s*\n(.*?)```", body, re.S)
    if not m:
        fail("No ```yaml block found in the issue.")

    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        fail(f"Couldn't parse the YAML: {e}")
    if isinstance(data, list):
        if len(data) != 1:
            fail("Submit exactly one link per issue.")
        data = data[0]
    if not isinstance(data, dict):
        fail("The YAML must describe a single link.")

    url = str(data.get("url", "")).strip()
    if not re.match(r"^https?://\S+$", url):
        fail("The link needs a `url` starting with http:// or https://.")

    entry = {"url": url}
    title = str(data.get("title") or "").strip() or fetch_title(url) or url
    entry["title"] = title
    if data.get("note"):
        entry["note"] = " ".join(str(data["note"]).split())
    tags = data.get("tags") or []
    if isinstance(tags, str):
        tags = tags.split(",")
    tags = sorted({re.sub(r"\s+", "-", str(t).strip().lower()) for t in tags if str(t).strip()})
    entry["tags"] = tags or ["inbox"]
    added = data.get("added") or datetime.date.today()
    try:
        entry["added"] = datetime.date.fromisoformat(str(added)[:10])
    except ValueError:
        entry["added"] = datetime.date.today()
    if data.get("found_via"):
        entry["found_via"] = str(data["found_via"]).strip()

    # Keep the file's existing formatting: append text rather than re-dumping everything.
    existing = ""
    if os.path.exists(LINKS_FILE):
        with open(LINKS_FILE, encoding="utf-8") as f:
            existing = f.read()
        current = yaml.safe_load(existing) or []
        if any(isinstance(l, dict) and l.get("url") == url for l in current):
            print(f"NOTE: {url} was already in {LINKS_FILE}; adding it again as requested.", file=sys.stderr)

    ordered = {k: entry[k] for k in FIELD_ORDER if k in entry}
    block = yaml.safe_dump([ordered], sort_keys=False, allow_unicode=True, width=10_000, default_flow_style=None)

    with open(LINKS_FILE, "a", encoding="utf-8") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        if existing.strip():
            f.write("\n")
        f.write(block)

    # Sanity check: the whole file must still parse.
    with open(LINKS_FILE, encoding="utf-8") as f:
        yaml.safe_load(f)

    print(title)


if __name__ == "__main__":
    main()
