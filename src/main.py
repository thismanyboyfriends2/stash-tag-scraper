#!/usr/bin/env python3
"""
StashDB Tag Scraper CLI

Fetches tag information from StashDB via GraphQL API and transfers to local Stash instance.
"""
import sys
import logging
import argparse

from graphql_client import StashDBClient
from stash_tags import transfer_tags
from models import Config

def fetch_and_transfer(config: Config, endpoint: str = "https://stashdb.org/graphql"):
    """Fetch tags from StashDB and transfer directly to Stash database."""
    # Initialize GraphQL client
    client = StashDBClient(
        endpoint=endpoint,
        api_key=config.stashdb_api_key
    )

    # Fetch all tags from StashDB
    logging.info("Fetching tags from StashDB GraphQL API...")
    tags = client.query_all_tags()
    logging.info(f"Fetched {len(tags)} tags")

    # Transfer to Stash database
    logging.info(f"Transferring tags to Stash database at {config.stash_db_path}...")
    transfer_tags(tags, config, endpoint)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='StashDB Tag Scraper - Fetch and transfer tags from StashDB to local Stash',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch and transfer tags
  %(prog)s

  # Use custom database path
  %(prog)s --stash-db /path/to/stash.db

  # Use custom API endpoint
  %(prog)s --endpoint https://custom.stashdb.org/graphql

  # Enable verbose logging
  %(prog)s --verbose
        """
    )

    parser.add_argument(
        '--api-key',
        help='StashDB API key (defaults to STASHDB_API_KEY env var)'
    )

    parser.add_argument(
        '--endpoint',
        default='https://stashdb.org/graphql',
        help='StashDB GraphQL endpoint (default: https://stashdb.org/graphql)'
    )

    parser.add_argument(
        '--stash-db',
        help='Path to Stash database (default: $STASH_DB_PATH or ~/.stash/stash-go.sqlite)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress all non-error output'
    )

    args = parser.parse_args()

    # Configure logging
    if args.quiet:
        log_level = logging.ERROR
    elif args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Execute command
    try:
        # Create and validate configuration (fails fast if config is wrong)
        try:
            config = Config.from_env(stash_db_path=args.stash_db)
        except (ValueError, FileNotFoundError) as e:
            logging.error(f"Configuration error: {e}")
            sys.exit(1)

        # Override API key if provided via CLI
        if args.api_key:
            config.stashdb_api_key = args.api_key

        # Fetch and transfer tags
        fetch_and_transfer(
            config=config,
            endpoint=args.endpoint
        )

        logging.info("All operations completed successfully")

    except KeyboardInterrupt:
        logging.info("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logging.error(f"Operation failed: {e}")
        if args.verbose:
            logging.exception("Full traceback:")
        sys.exit(1)


if __name__ == '__main__':
    main()
