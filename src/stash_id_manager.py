"""Module for managing stash IDs in the tag_stash_ids table."""
import sqlite3
import re
from datetime import datetime
from typing import List, Set, Tuple
import logging


def insert_tag_stash_ids(
    conn: sqlite3.Connection,
    tag_mappings: List[Tuple[int, str, str]],
    updated_at: str = None,
) -> None:
    """
    Insert stash ID mappings for newly created tags.

    Args:
        conn: Database connection
        tag_mappings: List of tuples (tag_id, endpoint, stash_id)
        updated_at: Optional timestamp. If not provided, uses current time.
    """
    if not tag_mappings:
        return

    # Get existing mappings to avoid duplicates
    existing = get_existing_stash_ids(conn)

    now = updated_at or datetime.now().isoformat(' ')
    rows = []

    for tag_id, endpoint, stash_id in tag_mappings:
        # Only add if this (tag_id, endpoint) pair doesn't already exist
        if (tag_id, endpoint) not in existing:
            rows.append((tag_id, endpoint, stash_id, now))

    if not rows:
        logging.info("No new stash ID mappings to insert (all already exist)")
        return

    with conn:
        cur = conn.cursor()
        cur.executemany("""
            INSERT INTO tag_stash_ids
            (tag_id, endpoint, stash_id, updated_at)
            VALUES (?, ?, ?, ?)
        """, rows)

    logging.info(f"Inserted {len(rows)} stash ID mappings")


def get_existing_stash_ids(conn: sqlite3.Connection) -> Set[Tuple[int, str]]:
    """
    Get all existing stash ID mappings to avoid duplicates.

    Args:
        conn: Database connection

    Returns:
        Set of (tag_id, endpoint) tuples
    """
    cur = conn.cursor()
    cur.execute("SELECT tag_id, endpoint FROM tag_stash_ids")
    return {(row[0], row[1]) for row in cur.fetchall()}


def migrate_existing_tags(conn: sqlite3.Connection, endpoint: str) -> None:
    """
    Migrate stash IDs from tag descriptions to tag_stash_ids table.

    Finds tags with URLs in their descriptions matching the pattern
    https://stashdb.org/tags/{stash_id}, extracts the stash_id, inserts
    into tag_stash_ids table, and cleans up the description.

    Args:
        conn: Database connection
        endpoint: The GraphQL endpoint (e.g., 'https://stashdb.org/graphql')
    """
    # Pattern to match StashDB URLs in descriptions
    url_pattern = re.compile(r'https://stashdb\.org/tags/([a-f0-9-]+)')

    # Fetch all tags with descriptions
    cur = conn.cursor()
    cur.execute("SELECT id, description FROM tags WHERE description IS NOT NULL")
    tags = cur.fetchall()

    stash_id_mappings = []
    description_updates = []
    now = datetime.now().isoformat(' ')

    for tag_id, description in tags:
        # Check if description contains a StashDB URL
        match = url_pattern.search(description)
        if match:
            stash_id = match.group(1)

            # Add to stash ID mappings
            stash_id_mappings.append((tag_id, endpoint, stash_id, now))

            # Clean up description by removing the URL line
            # Remove the URL and any preceding newline
            cleaned_description = url_pattern.sub('', description).rstrip()

            description_updates.append((cleaned_description, now, tag_id))

    if stash_id_mappings:
        with conn:
            cur = conn.cursor()
            # Insert stash ID mappings
            cur.executemany("""
                INSERT OR IGNORE INTO tag_stash_ids
                (tag_id, endpoint, stash_id, updated_at)
                VALUES (?, ?, ?, ?)
            """, stash_id_mappings)

            # Update descriptions
            if description_updates:
                cur.executemany("""
                    UPDATE tags SET description = ?, updated_at = ? WHERE id = ?
                """, description_updates)

        logging.info(f"Migrated {len(stash_id_mappings)} stash IDs from tag descriptions")
    else:
        logging.info("No existing tags with stash IDs found to migrate")
