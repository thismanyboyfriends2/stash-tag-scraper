"""Module for creating tags in the Stash database."""
import sqlite3
from datetime import datetime
from typing import List, Set
import logging

from models import Tag


def create_tags(conn: sqlite3.Connection, tags: List[Tag]):
    """Create new tags in the Stash database."""
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
            tag.get_description_with_url(),
            0,  # ignore_auto_tag default to False
            0,  # favorite default to False
            None,  # sort_name
        ))

    if tag_rows:
        with conn:
            cur = conn.cursor()
            cur.executemany("""
                INSERT OR IGNORE INTO tags
                (name, created_at, updated_at, description, ignore_auto_tag, favorite, sort_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, tag_rows)
        logging.info(f"Created {len(tag_rows)} new tags")


def find_new_tags(existing_names: Set[str], tags: List[Tag]) -> List[Tag]:
    """Find tags that don't already exist in the database."""
    existing_set = {name.lower() for name in existing_names if name}
    return [tag for tag in tags if tag.name and tag.name.lower() not in existing_set]


def get_existing_tag_names(conn: sqlite3.Connection) -> Set[str]:
    """Get all existing tag names from the database."""
    cur = conn.cursor()
    cur.execute("SELECT name FROM tags")
    return {row['name'] for row in cur.fetchall()}
