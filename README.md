# Zotero Skill for OpenClaw

An OpenClaw skill for full read/write management of Zotero libraries.

## Setup

1. Enable Zotero's local API: **Settings → Advanced → "Allow other applications..."**
2. Install the [debug-bridge plugin](https://github.com/retorquere/zotero-better-bibtex/releases/tag/debug-bridge) for write operations
3. Set a token in Zotero: **Settings → Advanced → Config Editor** → create `extensions.zotero.debug-bridge.token`
4. Save your token: `mkdir -p ~/.config/zotero-bridge && echo "YOUR_TOKEN" > ~/.config/zotero-bridge/token`

## Features

### Read (via Local API)
- List collections, search items, get item details

### Write (via Debug Bridge)
- Create/delete collections
- Add/remove items from collections
- Import papers by DOI, RIS file, or metadata
- Update item fields, add tags
- Execute arbitrary Zotero JS

## Usage

```bash
# Read
python3 scripts/zotero_helper.py list_collections
python3 scripts/zotero_helper.py search "CRISPR"
python3 scripts/zotero_helper.py get_item ABCD1234

# Write
python3 scripts/zotero_helper.py create_collection "My Papers" --parent PARENTKEY
python3 scripts/zotero_helper.py move_items COLLKEY ITEM1 ITEM2
python3 scripts/zotero_helper.py delete_items KEY1 KEY2
python3 scripts/zotero_helper.py add_tags ITEMKEY tag1 tag2
python3 scripts/zotero_helper.py update_field ITEMKEY title "New Title"

# Import
python3 scripts/zotero_helper.py import_doi 10.1038/s41586-020-2649-2
python3 scripts/zotero_helper.py import_ris papers.ris

# Escape hatch
python3 scripts/zotero_helper.py execute 'return Zotero.Libraries.userLibraryID'
```

## How It Works

- **Reads**: Local API at `http://localhost:23119/api/users/0/` (GET only)
- **Imports**: `POST /connector/import` with RIS data
- **Writes**: `POST /debug-bridge/execute` with JavaScript (requires debug-bridge plugin)

## Requirements

- Zotero 7+ desktop running locally
- Python 3.x (stdlib only, no pip dependencies)
- [debug-bridge plugin](https://github.com/retorquere/zotero-better-bibtex/releases/tag/debug-bridge) for write operations

## License

MIT
