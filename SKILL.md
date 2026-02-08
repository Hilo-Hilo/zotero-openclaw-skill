# Zotero Skill

Manage Hanson's Zotero library via the local API at `http://localhost:23119`.

## Key Facts

- Local API (`/api/users/0/...`) is **READ-ONLY** (GET only)
- To **create items**, use `POST /connector/import` with RIS data
- Helper script: `scripts/zotero_helper.py` (stdlib only)

## Helper Script Usage

```bash
# List all collections
python3 /Users/hansonwen/moltbot/skills/zotero/scripts/zotero_helper.py list_collections

# Search items
python3 /Users/hansonwen/moltbot/skills/zotero/scripts/zotero_helper.py search "CRISPR"

# Get specific item by key
python3 /Users/hansonwen/moltbot/skills/zotero/scripts/zotero_helper.py get_item ABCD1234

# Import RIS from file
python3 /Users/hansonwen/moltbot/skills/zotero/scripts/zotero_helper.py import_ris /path/to/file.ris

# Import a paper by DOI
python3 /Users/hansonwen/moltbot/skills/zotero/scripts/zotero_helper.py import_doi 10.1038/s41586-020-2649-2

# Import by metadata (title + authors + year)
python3 /Users/hansonwen/moltbot/skills/zotero/scripts/zotero_helper.py import_meta --title "Paper Title" --authors "Smith, J.;Doe, A." --year 2024 --journal "Nature" --doi "10.1234/example"
```

## Direct API Examples

```bash
# List collections
curl http://localhost:23119/api/users/0/collections

# Search items
curl "http://localhost:23119/api/users/0/items?q=neural+network"

# Get item
curl http://localhost:23119/api/users/0/items/ITEMKEY

# Import RIS (creates item)
curl -X POST http://localhost:23119/connector/import \
  -H "Content-Type: application/x-research-info-systems" \
  -d 'TY  - JOUR
AU  - Smith, John
TI  - Example Paper
JO  - Nature
PY  - 2024
DO  - 10.1234/example
ER  - '
```

## Notes

- Zotero desktop must be running for the local API to work
- The connector/import endpoint returns 201 on success
- Items appear in the default library (no collection assignment via this API)
- For collection management, use the Zotero desktop UI
