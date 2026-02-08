#!/usr/bin/env python3
"""Zotero local API helper with full CRUD via debug-bridge.

Read commands use the local REST API.
Write commands use the debug-bridge plugin (POST /debug-bridge/execute).

Usage:
    python3 zotero_helper.py list_collections
    python3 zotero_helper.py search "query"
    python3 zotero_helper.py get_item ITEMKEY
    python3 zotero_helper.py import_ris /path/to/file.ris
    python3 zotero_helper.py import_doi 10.1038/xxxxx
    python3 zotero_helper.py import_meta --title "..." --authors "A;B" --year 2024
    python3 zotero_helper.py create_collection "Name" [--parent KEY]
    python3 zotero_helper.py delete_items KEY1 KEY2 ...
    python3 zotero_helper.py move_items COLLECTION_KEY ITEM1 ITEM2 ...
    python3 zotero_helper.py remove_from_collection COLLECTION_KEY ITEM1 ITEM2 ...
    python3 zotero_helper.py delete_collection KEY
    python3 zotero_helper.py update_field ITEM_KEY FIELD VALUE
    python3 zotero_helper.py add_tags ITEM_KEY TAG1 TAG2 ...
    python3 zotero_helper.py execute "return Zotero.Libraries.getAll().length"
"""

import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
import argparse

BASE = "http://localhost:23119"
API = f"{BASE}/api/users/0"
BRIDGE = f"{BASE}/debug-bridge/execute"


def _get_token():
    token = os.environ.get("ZOTERO_BRIDGE_TOKEN")
    if token:
        return token.strip()
    token_path = os.path.expanduser("~/.config/zotero-bridge/token")
    try:
        with open(token_path) as f:
            return f.read().strip()
    except FileNotFoundError:
        print("Error: No debug-bridge token. Set ZOTERO_BRIDGE_TOKEN or create ~/.config/zotero-bridge/token", file=sys.stderr)
        sys.exit(1)


def _get(path):
    url = f"{API}{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def _execute_js(js_code):
    """Execute JavaScript in Zotero via debug-bridge."""
    token = _get_token()
    data = js_code.encode("utf-8")
    req = urllib.request.Request(
        BRIDGE,
        data=data,
        headers={
            "Content-Type": "text/plain",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode()
            try:
                parsed = json.loads(body)
                if isinstance(parsed, list) and len(parsed) >= 3:
                    status, content_type, result = parsed[0], parsed[1], parsed[2]
                    if status == 201:
                        return result
                    else:
                        print(f"Error (status {status}): {result}", file=sys.stderr)
                        sys.exit(1)
                return parsed
            except json.JSONDecodeError:
                return body
    except urllib.error.HTTPError as e:
        print(f"Bridge error: {e.code} {e.read().decode()}", file=sys.stderr)
        sys.exit(1)


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


# --- Write commands via debug-bridge ---

def create_collection(name, parent_key=None):
    parent_js = f'"{parent_key}"' if parent_key else "false"
    js = f'''
var col = new Zotero.Collection();
col.name = {json.dumps(name)};
col.parentKey = {parent_js};
await col.saveTx();
return JSON.stringify({{key: col.key, name: col.name}});
'''
    result = _execute_js(js)
    try:
        info = json.loads(result) if isinstance(result, str) else result
        print(f"Created collection: {info.get('name', name)} [{info.get('key', '?')}]")
        return info
    except (json.JSONDecodeError, TypeError):
        print(f"Result: {result}")
        return result


def delete_items(keys):
    keys_js = json.dumps(keys)
    js = f'''
var keys = {keys_js};
var results = [];
for (var k of keys) {{
    var item = await Zotero.Items.getByLibraryAndKeyAsync(1, k);
    if (item) {{
        item.deleted = true;
        await item.saveTx();
        results.push({{key: k, status: "trashed"}});
    }} else {{
        results.push({{key: k, status: "not_found"}});
    }}
}}
return JSON.stringify(results);
'''
    result = _execute_js(js)
    try:
        items = json.loads(result) if isinstance(result, str) else result
        for r in items:
            print(f"  {r['key']}: {r['status']}")
    except (json.JSONDecodeError, TypeError):
        print(f"Result: {result}")


def move_items(collection_key, item_keys):
    keys_js = json.dumps(item_keys)
    js = f'''
var col = await Zotero.Collections.getByLibraryAndKeyAsync(1, "{collection_key}");
if (!col) return JSON.stringify({{error: "Collection not found"}});
var keys = {keys_js};
var results = [];
for (var k of keys) {{
    var item = await Zotero.Items.getByLibraryAndKeyAsync(1, k);
    if (item) {{
        col.addItem(item.id);
        results.push({{key: k, status: "added"}});
    }} else {{
        results.push({{key: k, status: "not_found"}});
    }}
}}
await col.saveTx();
return JSON.stringify(results);
'''
    result = _execute_js(js)
    try:
        items = json.loads(result) if isinstance(result, str) else result
        if isinstance(items, dict) and "error" in items:
            print(f"Error: {items['error']}", file=sys.stderr)
            return
        for r in items:
            print(f"  {r['key']}: {r['status']}")
    except (json.JSONDecodeError, TypeError):
        print(f"Result: {result}")


def remove_from_collection(collection_key, item_keys):
    keys_js = json.dumps(item_keys)
    js = f'''
var col = await Zotero.Collections.getByLibraryAndKeyAsync(1, "{collection_key}");
if (!col) return JSON.stringify({{error: "Collection not found"}});
var keys = {keys_js};
var results = [];
for (var k of keys) {{
    var item = await Zotero.Items.getByLibraryAndKeyAsync(1, k);
    if (item) {{
        col.removeItem(item.id);
        results.push({{key: k, status: "removed"}});
    }} else {{
        results.push({{key: k, status: "not_found"}});
    }}
}}
await col.saveTx();
return JSON.stringify(results);
'''
    result = _execute_js(js)
    try:
        items = json.loads(result) if isinstance(result, str) else result
        if isinstance(items, dict) and "error" in items:
            print(f"Error: {items['error']}", file=sys.stderr)
            return
        for r in items:
            print(f"  {r['key']}: {r['status']}")
    except (json.JSONDecodeError, TypeError):
        print(f"Result: {result}")


def delete_collection(key):
    js = f'''
var col = await Zotero.Collections.getByLibraryAndKeyAsync(1, "{key}");
if (!col) return JSON.stringify({{error: "Collection not found"}});
var name = col.name;
await col.eraseTx();
return JSON.stringify({{key: "{key}", name: name, status: "deleted"}});
'''
    result = _execute_js(js)
    try:
        info = json.loads(result) if isinstance(result, str) else result
        if "error" in info:
            print(f"Error: {info['error']}", file=sys.stderr)
        else:
            print(f"Deleted collection: {info.get('name', '?')} [{key}]")
    except (json.JSONDecodeError, TypeError):
        print(f"Result: {result}")


def update_field(item_key, field, value):
    js = f'''
var item = await Zotero.Items.getByLibraryAndKeyAsync(1, "{item_key}");
if (!item) return JSON.stringify({{error: "Item not found"}});
item.setField({json.dumps(field)}, {json.dumps(value)});
await item.saveTx();
return JSON.stringify({{key: "{item_key}", field: {json.dumps(field)}, value: {json.dumps(value)}, status: "updated"}});
'''
    result = _execute_js(js)
    try:
        info = json.loads(result) if isinstance(result, str) else result
        if "error" in info:
            print(f"Error: {info['error']}", file=sys.stderr)
        else:
            print(f"Updated {field} = {value} on [{item_key}]")
    except (json.JSONDecodeError, TypeError):
        print(f"Result: {result}")


def add_tags(item_key, tags):
    js = f'''
var item = await Zotero.Items.getByLibraryAndKeyAsync(1, "{item_key}");
if (!item) return JSON.stringify({{error: "Item not found"}});
var tags = {json.dumps(tags)};
for (var t of tags) {{
    item.addTag(t);
}}
await item.saveTx();
return JSON.stringify({{key: "{item_key}", tags_added: tags, status: "updated"}});
'''
    result = _execute_js(js)
    try:
        info = json.loads(result) if isinstance(result, str) else result
        if "error" in info:
            print(f"Error: {info['error']}", file=sys.stderr)
        else:
            print(f"Added tags {tags} to [{item_key}]")
    except (json.JSONDecodeError, TypeError):
        print(f"Result: {result}")


def execute(js_code):
    result = _execute_js(js_code)
    print(result)


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

    # Write commands
    p = sub.add_parser("create_collection")
    p.add_argument("name")
    p.add_argument("--parent", default=None, help="Parent collection key")

    p = sub.add_parser("delete_items")
    p.add_argument("keys", nargs="+")

    p = sub.add_parser("move_items")
    p.add_argument("collection_key")
    p.add_argument("item_keys", nargs="+")

    p = sub.add_parser("remove_from_collection")
    p.add_argument("collection_key")
    p.add_argument("item_keys", nargs="+")

    p = sub.add_parser("delete_collection")
    p.add_argument("key")

    p = sub.add_parser("update_field")
    p.add_argument("item_key")
    p.add_argument("field")
    p.add_argument("value")

    p = sub.add_parser("add_tags")
    p.add_argument("item_key")
    p.add_argument("tags", nargs="+")

    p = sub.add_parser("execute")
    p.add_argument("js_code")

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
    elif args.command == "create_collection":
        create_collection(args.name, args.parent)
    elif args.command == "delete_items":
        delete_items(args.keys)
    elif args.command == "move_items":
        move_items(args.collection_key, args.item_keys)
    elif args.command == "remove_from_collection":
        remove_from_collection(args.collection_key, args.item_keys)
    elif args.command == "delete_collection":
        delete_collection(args.key)
    elif args.command == "update_field":
        update_field(args.item_key, args.field, args.value)
    elif args.command == "add_tags":
        add_tags(args.item_key, args.tags)
    elif args.command == "execute":
        execute(args.js_code)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
