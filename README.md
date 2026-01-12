# Stash Tag Scraper

Fetches tags from [StashDB](https://stashdb.org) and transfers them directly to your local Stash instance via GraphQL.

## Requirements

- Python 3.12+
- StashDB account and API key ([register here](https://stashdb.org/register))
- Local Stash instance running (GraphQL API enabled)

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

3. Set environment variables:
   ```bash
   export STASHDB_API_KEY="your-stashdb-api-key"
   export STASH_ENDPOINT="http://localhost:9999"  # optional, defaults to this
   ```

   Or create a `.env` file with these variables (see `.env.example`)

## Usage

### Quick Start

Run the script:

```bash
python src/main.py
```

### Command-Line Options

```bash
usage: main.py [-h] [--api-key API_KEY] [--endpoint ENDPOINT]
               [--verbose] [--quiet]

Options:
  --api-key API_KEY     StashDB API key (defaults to STASHDB_API_KEY env var)
  --endpoint ENDPOINT   StashDB GraphQL endpoint (default: https://stashdb.org/graphql)
  -v, --verbose         Enable verbose logging with detailed output
  -q, --quiet           Suppress all non-error output
  -h, --help            Show this help message
```

## Configuration

### Required Environment Variables

- `STASHDB_API_KEY`: Your StashDB API key (get from [StashDB register](https://stashdb.org/register))

### Optional Environment Variables

- `STASH_ENDPOINT`: Your local Stash GraphQL endpoint (default: `http://localhost:9999`)
- `STASH_API_KEY`: API key for local Stash authentication (only if your Stash requires it)

## Notes

- **No Database Access**: Tool communicates via GraphQL API only—no direct database access needed
- **Deleted Tags**: Automatically filters out deleted tags from StashDB
- **Case-Insensitive Matching**: Tags matched by name ignore case to prevent duplicates

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - See LICENSE file for details
