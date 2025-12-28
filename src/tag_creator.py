"""Module for creating tags in the Stash database."""
import sqlite3
from datetime import datetime
from typing import List, Set, Tuple, Dict
import logging

from models import Tag
from stash_id_manager import insert_tag_stash_ids


def create_tags(conn: sqlite3.Connection, tags: List[Tag], endpoint: str) -> Dict[str, int]:
    """
    Create new tags in the Stash database and insert stash IDs.

    Args:
        conn: Database connection
        tags: List of Tag objects to create
        endpoint: GraphQL endpoint for stash ID mapping

    Returns:
        Dictionary mapping tag names to tag IDs
    """
    existing_names = get_existing_tag_names(conn)
    new_tags = find_new_tags(existing_names, tags)

    skipped = len(tags) - len(new_tags)
    if skipped:
        logging.info(f"Skipped {skipped} duplicate tags")

    now = datetime.now().isoformat(' ')
    tag_rows = []
    for tag in new_tags:
        tag_rows.append((
            tag.name,
            now,  # created_at
            now,  # updated_at
            tag.description,  # Just the description, no URL
            0,  # ignore_auto_tag default to False
            0,  # favorite default to False
            None,  # sort_name
        ))

    tags_by_name = {}
    if tag_rows:
        with conn:
            cur = conn.cursor()
            cur.executemany("""
                INSERT OR IGNORE INTO tags
                (name, created_at, updated_at, description, ignore_auto_tag, favorite, sort_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, tag_rows)
        logging.info(f"Created {len(tag_rows)} new tags")

        # Fetch the newly created tag IDs
        created_tag_ids = get_newly_created_tag_ids(conn, [tag.name for tag in new_tags])
        tags_by_name = created_tag_ids

        # Insert stash IDs for newly created tags
        stash_id_mappings = [
            (created_tag_ids[tag.name], endpoint, tag.stash_id)
            for tag in new_tags
            if tag.name in created_tag_ids
        ]
        if stash_id_mappings:
            insert_tag_stash_ids(conn, stash_id_mappings, updated_at=now)

    return tags_by_name


def find_new_tags(existing_names: Set[str], tags: List[Tag]) -> List[Tag]:
    """Find tags that don't already exist in the database."""
    existing_set = {name.lower() for name in existing_names if name}
    return [tag for tag in tags if tag.name and tag.name.lower() not in existing_set]


def get_existing_tag_names(conn: sqlite3.Connection) -> Set[str]:
    """Get all existing tag names from the database."""
    cur = conn.cursor()
    cur.execute("SELECT name FROM tags")
    return {row['name'] for row in cur.fetchall()}


def get_newly_created_tag_ids(conn: sqlite3.Connection, tag_names: List[str]) -> Dict[str, int]:
    """
    Get the database IDs for newly created tags.

    Args:
        conn: Database connection
        tag_names: List of tag names to look up

    Returns:
        Dictionary mapping tag name to tag ID
    """
    if not tag_names:
        return {}

    cur = conn.cursor()
    placeholders = ','.join('?' * len(tag_names))
    cur.execute(f"SELECT id, name FROM tags WHERE name IN ({placeholders})", tag_names)
    return {row['name']: row['id'] for row in cur.fetchall()}
