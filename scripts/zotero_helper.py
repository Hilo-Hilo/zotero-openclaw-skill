#!/usr/bin/env python3
"""Zotero local API helper. Stdlib only (no pip dependencies).

Usage:
    python3 zotero_helper.py list_collections
    python3 zotero_helper.py search "query"
    python3 zotero_helper.py get_item ITEMKEY
    python3 zotero_helper.py import_ris /path/to/file.ris
    python3 zotero_helper.py import_doi 10.1038/xxxxx
    python3 zotero_helper.py import_meta --title "..." --authors "A;B" --year 2024 [--journal "..."] [--doi "..."]
"""

import json
import sys
import urllib.request
import urllib.parse
import urllib.error
import argparse

BASE = "http://localhost:23119"
API = f"{BASE}/api/users/0"


def _get(path):
    url = f"{API}{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def _post_ris(ris_text):
    req = urllib.request.Request(
        f"{BASE}/connector/import",
        data=ris_text.encode("utf-8"),
        headers={"Content-Type": "application/x-research-info-systems"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, resp.read().decode()


def list_collections():
    data = _get("/collections")
    for c in data:
        d = c["data"]
        parent = f" (parent: {d['parentCollection']})" if d.get("parentCollection") else ""
        print(f"  {d['key']}  {d['name']}{parent}")


def search_items(query):
    data = _get(f"/items?q={urllib.parse.quote(query)}")
    _print_items(data)


def get_item(key):
    data = _get(f"/items/{key}")
    print(json.dumps(data.get("data", data), indent=2, ensure_ascii=False))


def _print_items(items):
    for item in items:
        d = item.get("data", item)
        itype = d.get("itemType", "?")
        if itype == "attachment":
            continue
        title = d.get("title", "(no title)")
        creators = d.get("creators", [])
        authors = ", ".join(
            c.get("lastName", c.get("name", "?")) for c in creators[:3]
        )
        if len(creators) > 3:
            authors += " et al."
        year = d.get("date", "")[:4]
        key = d.get("key", "?")
        print(f"  [{key}] {title}")
        if authors:
            print(f"         {authors} ({year})")


def generate_ris(title, authors=None, year=None, journal=None, doi=None, item_type="JOUR"):
    """Generate RIS-formatted string from metadata."""
    lines = [f"TY  - {item_type}"]
    if authors:
        for a in authors.split(";"):
            lines.append(f"AU  - {a.strip()}")
    lines.append(f"TI  - {title}")
    if journal:
        lines.append(f"JO  - {journal}")
    if year:
        lines.append(f"PY  - {year}")
    if doi:
        lines.append(f"DO  - {doi}")
    lines.append("ER  - ")
    return "\n".join(lines)


def import_ris(ris_text):
    status, body = _post_ris(ris_text)
    print(f"Status: {status}")
    if body.strip():
        print(body)


def import_doi(doi):
    """Fetch citation metadata from doi.org and import as RIS."""
    req = urllib.request.Request(
        f"https://doi.org/{doi}",
        headers={"Accept": "application/x-research-info-systems"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            ris_text = resp.read().decode("utf-8")
        print(f"Fetched RIS for DOI {doi}")
        import_ris(ris_text)
    except urllib.error.HTTPError as e:
        print(f"Failed to fetch DOI: {e.code} {e.reason}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Zotero local API helper")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list_collections")

    p = sub.add_parser("search")
    p.add_argument("query")

    p = sub.add_parser("get_item")
    p.add_argument("key")

    p = sub.add_parser("import_ris")
    p.add_argument("file", help="Path to .ris file")

    p = sub.add_parser("import_doi")
    p.add_argument("doi")

    p = sub.add_parser("import_meta")
    p.add_argument("--title", required=True)
    p.add_argument("--authors", default=None, help="Semicolon-separated")
    p.add_argument("--year", default=None)
    p.add_argument("--journal", default=None)
    p.add_argument("--doi", default=None)

    args = parser.parse_args()

    if args.command == "list_collections":
        list_collections()
    elif args.command == "search":
        search_items(args.query)
    elif args.command == "get_item":
        get_item(args.key)
    elif args.command == "import_ris":
        with open(args.file) as f:
            import_ris(f.read())
    elif args.command == "import_doi":
        import_doi(args.doi)
    elif args.command == "import_meta":
        ris = generate_ris(args.title, args.authors, args.year, args.journal, args.doi)
        print(f"Generated RIS:\n{ris}\n")
        import_ris(ris)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
