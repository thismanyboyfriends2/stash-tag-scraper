# Stash Tag Scraper

A Python tool to fetch tag information from [StashDB](https://stashdb.org) and transfer it directly to your local Stash instance.

## Overview

This tool uses the StashDB GraphQL API to fetch thousands of tags with complete information (name, description, aliases, categories) and intelligently transfers them to your local Stash database with proper deduplication and categorization.

## Features

- **Fast GraphQL-based fetching**: Downloads ~3000 tags in seconds
- **Smart deduplication**: Avoids creating duplicate tags
- **Alias management**: Creates tag aliases while preventing conflicts
- **Category hierarchies**: Creates parent-child relationships between tags and categories
- **Conflict logging**: Saves skipped aliases to JSON for manual review

## Requirements

- Python 3.10+
- StashDB account and API key ([register here](https://stashdb.org/register))
- Local Stash instance

## Installation

1. Clone this repository:

  ```bash
  git clone https://github.com/thismanyboyfriends/stash-tag-scraper.git
  cd stash-tag-scraper
  ```

2. Install dependencies:

  ```bash
  pip install -r requirements.txt
  ```

3. Set your StashDB API key:

  ```bash
  export STASHDB_API_KEY="your-api-key-here"
  ```

Alternatively, create a `.env` file (see `.env.example`).

## Usage

### Quick Start

Run the script:

```bash
python src/main.py
```

### Command-Line Options

```bash
usage: main.py [-h] [--api-key API_KEY] [--endpoint ENDPOINT]
               [--stash-db STASH_DB] [--per-page PER_PAGE]
               [--verbose] [--quiet]

Options:
  --api-key API_KEY     StashDB API key (defaults to STASHDB_API_KEY env var)
  --endpoint ENDPOINT   StashDB GraphQL endpoint
  --stash-db STASH_DB   Path to Stash database (default: ~/.stash/stash-go.sqlite)
  -v, --verbose         Enable verbose logging
  -q, --quiet           Suppress non-error output
  -h, --help            Show this help message
```

## Configuration

### Environment Variables

- `STASHDB_API_KEY` (required): Your StashDB API key
- `STASH_DB_PATH` (optional): Path to Stash database (default: `~/.stash/stash-go.sqlite`)

## How It Works

### Architecture

The tool works in two stages:

1. **Fetch**: Downloads all tags from StashDB using the GraphQL API
2. **Transfer**: Directly transfers tags to your local Stash database

### Transfer Process

The transfer executes these operations in sequence:

1. **Create Tags**: Inserts new tags, skipping duplicates (case-insensitive matching)
2. **Enrich Tags**: Updates descriptions for newly created tags
3. **Create Aliases**: Creates tag aliases while avoiding conflicts with existing tag names
4. **Categorize Tags**: Creates parent-child relationships between tags and their categories

### Category Format

Categories follow the pattern `category:*` (e.g., Acts" becomes `category:acts`). Tags are automatically linked to their category parents.

### Conflict Handling

When an alias conflicts with an existing tag name, it's skipped and logged to `output/skipped_aliases.json` with enriched information including:

- The alias that was skipped
- The existing tag it conflicts with
- A direct link to view the conflict in Stash

This allows for manual review and resolution of conflicts.

## Important Notes

- **API Key Required**: You must register at [StashDB](https://stashdb.org/register) to get an API key
- **Duplicate Handling**: Tags are deduplicated by name (case-insensitive)
- **Backup Recommended**: Consider backing up your Stash database before running transfers
- **Deleted Tags**: Automatically filters out deleted tags from StashDB

**Permission Issues:**

- Ensure you have write access to the Stash database
- Make sure Stash is not running during the transfer

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - See LICENSE file for details
