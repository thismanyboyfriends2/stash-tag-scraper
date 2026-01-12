#!/usr/bin/env python3
"""
StashDB Tag Scraper CLI

Fetches tag information from StashDB via GraphQL API and transfers to local Stash.
"""
import sys
import logging
import argparse
import asyncio

from rich.logging import RichHandler

from graphql_client import StashDBClient
from stash_tags import transfer_tags_graphql
from stash_client import StashClient
from models import Config, StashConnection

async def fetch_and_transfer(config: Config, endpoint: str = "https://stashdb.org/graphql", use_cache: bool = True):
    """Fetch tags from StashDB and transfer to Stash via GraphQL."""
    logging.info("Fetching tags from StashDB GraphQL API...")
    client = StashDBClient(endpoint=endpoint, api_key=config.stashdb_api_key)
    tags = client.query_all_tags(use_cache=use_cache)
    logging.info(f"Fetched {len(tags)} tags from StashDB")

    logging.info("Connecting to local Stash GraphQL API...")
    stash_conn = StashConnection.from_env()

    async with StashClient(stash_conn) as stash_client:
        logging.info("Transferring tags to Stash...")
        await transfer_tags_graphql(stash_client, tags, config)

    logging.info("Transfer completed successfully")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='StashDB Tag Scraper - Fetch and transfer tags from StashDB to local Stash',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch and transfer tags
  %(prog)s

  # Use custom API endpoint
  %(prog)s --endpoint https://custom.stashdb.org/graphql

  # Enable verbose logging (app logs only)
  %(prog)s --verbose

  # Enable very verbose logging (includes library debug logs)
  %(prog)s -vv
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
        '--verbose', '-v',
        action='count',
        default=0,
        help='Enable verbose logging (-v for verbose, -vv for very verbose)'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress all non-error output'
    )

    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Do not use cached tags, always fetch from StashDB'
    )

    parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='Clear the tag cache and exit'
    )

    args = parser.parse_args()

    # Handle cache clearing early
    if args.clear_cache:
        StashDBClient.clear_cache()
        return

    if args.quiet:
        log_level = logging.ERROR
    elif args.verbose >= 1:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(
        level=log_level,
        format='%(message)s',
        handlers=[RichHandler(rich_tracebacks=True, show_time=True)]
    )

    # Suppress noisy library logs
    if args.quiet:
        logging.getLogger('httpx').setLevel(logging.ERROR)
        logging.getLogger('httpcore').setLevel(logging.ERROR)
        logging.getLogger('gql').setLevel(logging.ERROR)
        logging.getLogger('stash_graphql_client').setLevel(logging.ERROR)
    elif args.verbose >= 2:
        # Very verbose: show everything including stash_graphql_client
        pass
    else:
        # Normal or verbose mode: suppress library noise
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('httpcore').setLevel(logging.WARNING)
        logging.getLogger('gql').setLevel(logging.WARNING)
        logging.getLogger('stash_graphql_client').setLevel(logging.WARNING)

    try:
        try:
            config = Config.from_env()
        except ValueError as e:
            logging.error(f"Configuration error: {e}")
            sys.exit(1)

        if args.api_key:
            config.stashdb_api_key = args.api_key

        use_cache = not args.no_cache
        asyncio.run(fetch_and_transfer(config, args.endpoint, use_cache=use_cache))
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
