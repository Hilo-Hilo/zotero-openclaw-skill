# Zotero Skill for OpenClaw

An OpenClaw skill for managing Zotero libraries via the local API.

## Setup

1. Enable Zotero's local API: **Zotero → Settings → Advanced → "Allow other applications on this computer to communicate with Zotero"**
2. Copy `SKILL.md` and `scripts/` to your OpenClaw skills directory

## Features

- **Read**: List collections, search items, get item details
- **Write**: Import papers by DOI, RIS file, or metadata (title/authors/year)
- **Helper script**: `scripts/zotero_helper.py` (stdlib only, no pip dependencies)

## Usage

```bash
# List collections
python3 scripts/zotero_helper.py list_collections

# Search items
python3 scripts/zotero_helper.py search "CRISPR"

# Import by DOI
python3 scripts/zotero_helper.py import_doi 10.1038/s41586-020-2649-2

# Import RIS file
python3 scripts/zotero_helper.py import_ris papers.ris

# Import by metadata
python3 scripts/zotero_helper.py import_meta --title "Paper Title" --authors "Smith, J." --year 2024
```

## How It Works

- Local API at `http://localhost:23119/api/users/0/` is **read-only** (GET only)
- Item creation uses `POST /connector/import` with RIS-formatted data
- DOI import fetches RIS from `doi.org` content negotiation

## License

MIT
