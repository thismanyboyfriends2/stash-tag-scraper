"""Main orchestration module for transferring tags from StashDB to Stash."""
import sqlite3
import logging
from typing import List

from models import Tag, Config
from tag_creator import create_tags
from tag_enricher import enrich_tags_with_information
from alias_manager import create_tag_aliases
from category_manager import categorise_tags
from stash_id_manager import migrate_existing_tags


def transfer_tags(tags: List[Tag], config: Config, endpoint: str = "https://stashdb.org/graphql"):
    """
    Transfer tags from StashDB to local Stash database.

    Args:
        tags: List of Tag objects from StashDB
        config: Configuration object
        endpoint: GraphQL endpoint used for scraping
    """
    with sqlite3.connect(config.stash_db_path) as conn:
        conn.row_factory = sqlite3.Row

        # Migrate existing tags with stash IDs from descriptions
        logging.info("Migrating existing stash IDs from tag descriptions...")
        migrate_existing_tags(conn, endpoint)

        # Build lookup dictionary for efficient searching
        tags_by_name = {tag.name: tag for tag in tags}

        # Execute transfer steps in sequence
        create_tags(conn, tags, endpoint)
        enrich_tags_with_information(conn, tags_by_name, endpoint)
        create_tag_aliases(conn, tags, config)
        categorise_tags(conn, tags)
