"""Fill in missing notes (and hostname-only titles) in links.yml from each page's
own description, i.e. its <meta name="description"> / og:description tag.

Only empty fields are filled; anything typed by hand is left alone. Tags are
never touched. Only recently added links are checked, so a page with no
description isn't re-fetched forever.

Env:
  LINKS_FILE  path to links file (default links.yml)
  RECENT_DAYS only consider links added within this many days (default 7)
"""
import datetime
import html
import os
import re
import sys
import urllib.parse
import urllib.request

import yaml

LINKS_FILE = os.environ.get("LINKS_FILE", "links.yml")
RECENT_DAYS = int(os.environ.get("RECENT_DAYS", "7"))
FIELD_ORDER = ["url", "title", "note", "tags", "added", "found_via"]


# ---------- file format (matches the web page's output) ----------

class Dumper(yaml.SafeDumper):
    pass


Dumper.add_representer(str, lambda d, s: d.represent_scalar("tag:yaml.org,2002:str", s))
Dumper.add_representer(list, lambda d, v: d.represent_sequence("tag:yaml.org,2002:seq", v, flow_style=True))


def order(e):
    keys = FIELD_ORDER + [k for k in e if k not in FIELD_ORDER]
    out = {}
    for k in keys:
        v = e.get(k)
        if v is None or v == "" or v == []:
            continue
        if k == "added" and isinstance(v, str):
            try:
                v = datetime.date.fromisoformat(v[:10])
            except ValueError:
                pass
        out[k] = v
    return out


def dump_entry(e):
    """One link as a '- ' list item with block fields and inline tags (same as the web page)."""
    body = yaml.dump(order(e), Dumper=Dumper, sort_keys=False, allow_unicode=True,
                     width=100_000, default_flow_style=False)
    lines = body.rstrip("\n").split("\n")
    return "- " + "\n  ".join(lines) + "\n"


def dump_all(entries):
    return "\n".join(dump_entry(e) for e in entries)


# ---------- helpers ----------

def host(url):
    return re.sub(r"^www\.", "", urllib.parse.urlparse(url).hostname or url)


def added_date(e):
    try:
        return datetime.date.fromisoformat(str(e.get("added"))[:10])
    except ValueError:
        return None


def needs(e):
    want = []
    if not str(e.get("note") or "").strip():
        want.append("note")
    title = str(e.get("title") or "").strip()
    if not title or title in (host(e["url"]), e["url"]):
        want.append("title")
    return want


def fetch_meta(url):
    """Return (title, description) from the page, or ("", "") if it can't be read."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; link-collection/1.0)",
            "Accept": "text/html,application/xhtml+xml"})
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read(600_000).decode(r.headers.get_content_charset() or "utf-8", "ignore")
    except Exception as ex:
        print(f"  could not fetch page: {ex}", file=sys.stderr)
        return "", ""

    def meta(name):
        for tag in re.findall(r"<meta\b[^>]*>", raw, re.I | re.S):
            attrs = {k.lower(): v for k, _, v in
                     re.findall(r'([\w:-]+)\s*=\s*(["\'])(.*?)\2', tag, re.S)}
            if name in (attrs.get("name", "").lower(), attrs.get("property", "").lower()):
                return " ".join(html.unescape(attrs.get("content", "")).split())
        return ""

    t = re.search(r"<title[^>]*>(.*?)</title>", raw, re.S | re.I)
    title = meta("og:title") or (" ".join(html.unescape(t.group(1)).split()) if t else "")
    desc = meta("description") or meta("og:description") or meta("twitter:description")
    return title[:150], desc


def shorten(text, limit=300):
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",;:-–— ")
    return cut + "…"


# ---------- main ----------

def main():
    if not os.path.exists(LINKS_FILE):
        print("no links file; nothing to do")
        return
    with open(LINKS_FILE, encoding="utf-8") as f:
        entries = yaml.safe_load(f) or []

    since = datetime.date.today() - datetime.timedelta(days=RECENT_DAYS)
    changed = []
    for e in entries:
        if not isinstance(e, dict) or not e.get("url"):
            continue
        d = added_date(e)
        want = needs(e)
        if not want or (d and d < since):
            continue
        print(f"checking {e['url']} (missing: {', '.join(want)})")
        title, desc = fetch_meta(e["url"])
        did = False
        if "note" in want and desc:
            e["note"] = shorten(desc)
            did = True
        if "title" in want and title:
            e["title"] = title
            did = True
        if did:
            changed.append(e)
            print(f"  -> {e.get('title')} | {e.get('note')}")
        else:
            print("  page has no usable title/description; left as is")

    if not changed:
        print("nothing to fill in")
        return
    text = dump_all(entries)
    yaml.safe_load(text)  # must still parse
    with open(LINKS_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    titles = ", ".join(str(e.get("title")) for e in changed)
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"changed=true\nsummary=Auto-fill note: {titles[:200]}\n")
    print(f"filled in {len(changed)} link(s)")


if __name__ == "__main__":
    main()
