# Stash Tag Scraper

A Stash plugin that fetches tags from [StashDB](https://stashdb.org) and synchronises them directly to your local Stash instance.

## Requirements

- Python 3.12+
- Stash instance with GraphQL API enabled
- StashDB account and API key ([register here](https://stashdb.org/register))

## Installation

Follow these steps to install the plugin:

### Windows
```cmd
REM Create plugin directory
mkdir "C:\stash\plugins\stashdb-tag-sync"

REM Copy files (use File Explorer or these commands)
xcopy plugin\plugin.yml "C:\stash\plugins\stashdb-tag-sync\" /Y
xcopy plugin\stashdb_tag_sync.py "C:\stash\plugins\stashdb-tag-sync\" /Y
xcopy src "C:\stash\plugins\stashdb-tag-sync\src" /E /Y

REM Install dependencies
python -m pip install -r requirements.txt
```

### Linux/macOS
```bash
# Create plugin directory
mkdir -p ~/.stash/plugins/stashdb-tag-sync

# Copy plugin files
cp plugin/plugin.yml ~/.stash/plugins/stashdb-tag-sync/
cp plugin/stashdb_tag_sync.py ~/.stash/plugins/stashdb-tag-sync/
cp -r src ~/.stash/plugins/stashdb-tag-sync/

# Install dependencies
pip install -r requirements.txt
```

### Post-Installation Setup

After installing plugin files:

1. **Reload plugins in Stash UI:**
   - Go to Settings (gear icon, bottom right)
   - Click "Plugins"
   - Click "Reload" button
   - You should see "StashDB Tag Synchroniser" appear

2. **Configure plugin settings:**
   - In Settings > Plugins > StashDB Tag Synchroniser
   - Paste your StashDB API key (get from https://stashdb.org/register)
   - Optionally adjust other settings

3. **Run the plugin:**
   - Go to Tasks page
   - Find "Synchronise Tags from StashDB"
   - Click it to start synchronisation
   - Monitor progress in task log

### Plugin Configuration

Configure these settings via Stash UI:

- **StashDB API Key**: Your StashDB API key (required)
- **StashDB Endpoint**: GraphQL endpoint (default: https://stashdb.org/graphql)
- **Use Cache**: Cache tags for 24 hours (default: enabled)
- **Verbose Logging**: Enable debug logs (default: disabled)
- **Ignored Aliases File Path**: Path to file with aliases to exclude (optional)


## Notes

- **No Database Access**: Tool communicates via GraphQL API only—no direct database access needed
- **Deleted Tags**: Automatically filters out deleted tags from StashDB
- **Case-Insensitive Matching**: Tags matched by name ignore case to prevent duplicates

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - See LICENSE file for details
