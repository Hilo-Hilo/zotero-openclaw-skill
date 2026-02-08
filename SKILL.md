# Zotero Skill

Manage Hanson's Zotero library via the local API and debug-bridge plugin.

## Key Facts

- Local API (`/api/users/0/...`) is **READ-ONLY** (GET only)
- **Write operations** use the debug-bridge plugin (`POST /debug-bridge/execute`)
- Debug-bridge token: env var `ZOTERO_BRIDGE_TOKEN` or `~/.config/zotero-bridge/token`
- Helper script: `scripts/zotero_helper.py` (stdlib only, no pip)

## Helper Script Usage

```bash
ZOTERO=python3 /Users/hansonwen/moltbot/skills/zotero/scripts/zotero_helper.py

# --- Read Commands (local API) ---

# List all collections
$ZOTERO list_collections

# Search items
$ZOTERO search "CRISPR"

# Get specific item by key
$ZOTERO get_item ABCD1234

# Import RIS from file
$ZOTERO import_ris /path/to/file.ris

# Import a paper by DOI
$ZOTERO import_doi 10.1038/s41586-020-2649-2

# Import by metadata
$ZOTERO import_meta --title "Paper Title" --authors "Smith, J.;Doe, A." --year 2024 --journal "Nature"

# --- Write Commands (debug-bridge) ---

# Create a collection (optionally nested under parent)
$ZOTERO create_collection "My Collection"
$ZOTERO create_collection "Sub Collection" --parent PARENTKEY

# Delete/trash items by key
$ZOTERO delete_items KEY1 KEY2 KEY3

# Add items to a collection
$ZOTERO move_items COLLECTION_KEY ITEM1 ITEM2

# Remove items from a collection (doesn't delete them)
$ZOTERO remove_from_collection COLLECTION_KEY ITEM1 ITEM2

# Delete a collection (items are NOT deleted)
$ZOTERO delete_collection COLLKEY

# Update an item's metadata field
$ZOTERO update_field ITEMKEY title "New Title"
$ZOTERO update_field ITEMKEY date "2024-01-15"

# Add tags to an item
$ZOTERO add_tags ITEMKEY "machine-learning" "genomics"

# Run arbitrary JavaScript in Zotero (escape hatch)
$ZOTERO execute 'return Zotero.Libraries.getAll().length'
```

## Notes

- Zotero desktop must be running for all commands
- `delete_items` moves to trash (recoverable); `delete_collection` permanently removes the collection
- `move_items` adds items to a collection (items can be in multiple collections)
- The debug-bridge plugin must be installed with a matching token
